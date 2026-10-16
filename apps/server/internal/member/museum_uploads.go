package member

import (
	"bytes"
	"context"
	"encoding/binary"
	"errors"
	"fmt"
	"image"
	"image/jpeg"
	"image/png"
	"io"
	"net/http"
	"net/url"
	"regexp"
	"strings"
	"sync"

	"golang.org/x/oauth2/google"
)

const museumUploadLimit = 10 << 20

var ErrMuseumUploadLimit = errors.New("upload capacity reached")

type MuseumStudioOptions struct {
	Catalogue MuseumArtworkCatalogue
	Blobs     MuseumBlobStore
}
type MuseumUpload struct {
	ID          string `json:"id"`
	Key         string `json:"-"`
	ContentType string `json:"content_type"`
	Width       int    `json:"width"`
	Height      int    `json:"height"`
	Size        int    `json:"size"`
	URL         string `json:"url"`
}
type MuseumBlobStore interface {
	Put(context.Context, string, []byte, string) error
	Get(context.Context, string) ([]byte, error)
}
type memoryMuseumBlobs struct {
	mu    sync.Mutex
	items map[string][]byte
	size  int
}

func NewMemoryMuseumBlobs() MuseumBlobStore { return &memoryMuseumBlobs{items: map[string][]byte{}} }
func (s *memoryMuseumBlobs) Put(_ context.Context, key string, data []byte, _ string) error {
	s.mu.Lock()
	defer s.mu.Unlock()
	if s.size+len(data) > 128<<20 {
		return ErrMuseumUploadLimit
	}
	if _, ok := s.items[key]; ok {
		return ErrPublicationConflict
	}
	s.items[key] = append([]byte(nil), data...)
	s.size += len(data)
	return nil
}
func (s *memoryMuseumBlobs) Get(_ context.Context, key string) ([]byte, error) {
	s.mu.Lock()
	defer s.mu.Unlock()
	data, ok := s.items[key]
	if !ok {
		return nil, ErrPublicationMissing
	}
	return append([]byte(nil), data...), nil
}

// Use a dedicated private bucket, with no public IAM grants. Only this API serves images.
type GCSMuseumBlobs struct{ Bucket string }

func (s GCSMuseumBlobs) request(ctx context.Context, method, key, contentType string, data []byte) ([]byte, error) {
	if !regexp.MustCompile(`^[a-z0-9][a-z0-9.-]{1,220}[a-z0-9]$`).MatchString(s.Bucket) {
		return nil, errors.New("museum upload bucket is not configured")
	}
	client, err := google.DefaultClient(ctx, "https://www.googleapis.com/auth/devstorage.read_write")
	if err != nil {
		return nil, err
	}
	endpoint := "https://storage.googleapis.com/storage/v1/b/" + url.PathEscape(s.Bucket) + "/o/" + url.PathEscape(key) + "?alt=media"
	if method == "POST" {
		endpoint = "https://storage.googleapis.com/upload/storage/v1/b/" + url.PathEscape(s.Bucket) + "/o?" + url.Values{"uploadType": {"media"}, "name": {key}, "ifGenerationMatch": {"0"}}.Encode()
	}
	req, err := http.NewRequestWithContext(ctx, method, endpoint, bytes.NewReader(data))
	if err != nil {
		return nil, err
	}
	if contentType != "" {
		req.Header.Set("Content-Type", contentType)
	}
	response, err := client.Do(req)
	if err != nil {
		return nil, err
	}
	defer response.Body.Close()
	if response.StatusCode < 200 || response.StatusCode > 299 {
		return nil, fmt.Errorf("museum image storage status %d", response.StatusCode)
	}
	raw, err := io.ReadAll(io.LimitReader(response.Body, museumUploadLimit+1))
	if err != nil {
		return nil, err
	}
	if len(raw) > museumUploadLimit {
		return nil, ErrMuseumUploadLimit
	}
	return raw, nil
}
func (s GCSMuseumBlobs) Put(ctx context.Context, key string, data []byte, kind string) error {
	_, err := s.request(ctx, "POST", key, kind, data)
	return err
}
func (s GCSMuseumBlobs) Get(ctx context.Context, key string) ([]byte, error) {
	return s.request(ctx, "GET", key, "", nil)
}
func museumImageURL(slug, id string) string { return "/api/museum-media/" + slug + "/" + id }
func museumDocumentImageURL(slug string, d MuseumDocument) string {
	if d.ImageID != "" {
		return museumImageURL(slug, d.ImageID)
	}
	return d.ImageURL
}
func prepareMuseumImage(raw []byte) ([]byte, MuseumUpload, error) {
	var info MuseumUpload
	cfg, format, err := image.DecodeConfig(bytes.NewReader(raw))
	if err != nil || (format != "jpeg" && format != "png") {
		return nil, info, errors.New("Choose a JPEG or PNG image.")
	}
	if cfg.Width < 1 || cfg.Height < 1 || int64(cfg.Width)*int64(cfg.Height) > 20000000 {
		return nil, info, errors.New("Use an image with no more than 20 million pixels.")
	}
	picture, _, err := image.Decode(bytes.NewReader(raw))
	if err != nil {
		return nil, info, errors.New("This image could not be read. Try another JPEG or PNG.")
	}
	if format == "jpeg" {
		picture = orientMuseumImage(picture, jpegOrientation(raw))
	}
	var output bytes.Buffer
	// Re-encode decoded pixels: scripts, ancillary chunks and EXIF/location metadata do not survive.
	if format == "png" {
		err = png.Encode(&output, picture)
		info.ContentType = "image/png"
	} else {
		err = jpeg.Encode(&output, picture, &jpeg.Options{Quality: 92})
		info.ContentType = "image/jpeg"
	}
	if err != nil {
		return nil, info, err
	}
	if output.Len() > museumUploadLimit {
		return nil, info, errors.New("The processed image is too large. Choose a smaller image.")
	}
	info.Width = picture.Bounds().Dx()
	info.Height = picture.Bounds().Dy()
	info.Size = output.Len()
	return output.Bytes(), info, nil
}
func jpegOrientation(raw []byte) int {
	for pos := 2; pos+4 <= len(raw); {
		if raw[pos] != 0xff {
			return 1
		}
		marker := raw[pos+1]
		if marker == 0xda || marker == 0xd9 {
			return 1
		}
		length := int(binary.BigEndian.Uint16(raw[pos+2 : pos+4]))
		if length < 2 || pos+2+length > len(raw) {
			return 1
		}
		segment := raw[pos+4 : pos+2+length]
		pos += length + 2
		if marker != 0xe1 || len(segment) < 14 || string(segment[:6]) != "Exif\x00\x00" {
			continue
		}
		data := segment[6:]
		var order binary.ByteOrder
		if string(data[:2]) == "II" {
			order = binary.LittleEndian
		} else if string(data[:2]) == "MM" {
			order = binary.BigEndian
		} else {
			return 1
		}
		if order.Uint16(data[2:4]) != 42 {
			return 1
		}
		offset := int(order.Uint32(data[4:8]))
		if offset < 8 || offset+2 > len(data) {
			return 1
		}
		count := int(order.Uint16(data[offset : offset+2]))
		for i := 0; i < count; i++ {
			entry := offset + 2 + i*12
			if entry+12 > len(data) {
				return 1
			}
			if order.Uint16(data[entry:entry+2]) == 0x112 && order.Uint16(data[entry+2:entry+4]) == 3 && order.Uint32(data[entry+4:entry+8]) == 1 {
				value := int(order.Uint16(data[entry+8 : entry+10]))
				if value >= 1 && value <= 8 {
					return value
				}
				return 1
			}
		}
	}
	return 1
}
func orientMuseumImage(src image.Image, orientation int) image.Image {
	if orientation <= 1 || orientation > 8 {
		return src
	}
	b := src.Bounds()
	w, h := b.Dx(), b.Dy()
	ow, oh := w, h
	if orientation >= 5 {
		ow, oh = h, w
	}
	dst := image.NewNRGBA(image.Rect(0, 0, ow, oh))
	for y := 0; y < h; y++ {
		for x := 0; x < w; x++ {
			dx, dy := x, y
			switch orientation {
			case 2:
				dx = w - 1 - x
			case 3:
				dx, dy = w-1-x, h-1-y
			case 4:
				dy = h - 1 - y
			case 5:
				dx, dy = y, x
			case 6:
				dx, dy = h-1-y, x
			case 7:
				dx, dy = h-1-y, w-1-x
			case 8:
				dx, dy = y, w-1-x
			}
			dst.Set(dx, dy, src.At(b.Min.X+x, b.Min.Y+y))
		}
	}
	return dst
}
func (h *Handler) registerMuseumUploads(mux *http.ServeMux, store MuseumStudioStore, blobs MuseumBlobStore) {
	slots := make(chan struct{}, 2)
	mux.HandleFunc("POST /api/v1/member/museum-studio/{slug}/images", h.memberOnly(func(w http.ResponseWriter, r *http.Request, u User) {
		slug := r.PathValue("slug")
		if err := store.Access(r.Context(), u, slug); err != nil {
			museumStudioError(w, err)
			return
		}
		if blobs == nil {
			accessError(w, 503, "UPLOAD_UNAVAILABLE", "Image uploads are not configured yet.")
			return
		}
		select {
		case slots <- struct{}{}:
			defer func() { <-slots }()
		default:
			w.Header().Set("Retry-After", "3")
			accessError(w, 429, "UPLOAD_BUSY", "Another image is processing. Please try again shortly.")
			return
		}
		raw, err := io.ReadAll(http.MaxBytesReader(w, r.Body, museumUploadLimit))
		if err != nil {
			accessError(w, 413, "IMAGE_TOO_LARGE", "Use a JPEG or PNG image up to 10 MB.")
			return
		}
		data, info, err := prepareMuseumImage(raw)
		if err != nil {
			accessError(w, 400, "INVALID_IMAGE", err.Error())
			return
		}
		info.ID = studyID()
		info.Key = "museum-uploads/" + slug + "/" + info.ID
		info.URL = museumImageURL(slug, info.ID)
		if err = blobs.Put(r.Context(), info.Key, data, info.ContentType); err != nil {
			accessError(w, 503, "UPLOAD_FAILED", "The image could not be stored. Try again or use an image URL.")
			return
		}
		if err = store.SaveUpload(r.Context(), u, slug, info); err != nil {
			museumStudioError(w, err)
			return
		}
		bookmarkJSON(w, info)
	}))
	mux.HandleFunc("GET /api/v1/museum-media/{slug}/{id}", museumPublicRead(func(w http.ResponseWriter, r *http.Request) {
		slug, id := r.PathValue("slug"), r.PathValue("id")
		if !bookmarkID.MatchString(id) || blobs == nil {
			museumStudioError(w, ErrPublicationMissing)
			return
		}
		info, err := store.Upload(r.Context(), slug, id)
		if err != nil {
			museumStudioError(w, err)
			return
		}
		public, err := store.ImagePublished(r.Context(), slug, id)
		if err != nil {
			museumStudioError(w, err)
			return
		}
		if !public {
			u, ok := h.authorize(w, r)
			if !ok {
				return
			}
			if err = store.Access(r.Context(), u, slug); err != nil {
				museumStudioError(w, err)
				return
			}
		}
		raw, err := blobs.Get(r.Context(), info.Key)
		if err != nil {
			museumStudioError(w, err)
			return
		}
		w.Header().Set("Content-Type", info.ContentType)
		w.Header().Set("X-Content-Type-Options", "nosniff")
		w.Header().Set("Content-Security-Policy", "default-src 'none'; sandbox")
		w.Header().Set("Content-Disposition", `inline; filename="museum-image.`+strings.TrimPrefix(info.ContentType, "image/")+`"`)
		w.Write(raw)
	}))
}
