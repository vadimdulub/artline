package member

import "net/http"

// A shared link grants reading only, independently of account sessions. No public
// mutation or directory route exists. The token lookup is uniquely indexed.
func (h *Handler) registerSharedStudies(mux *http.ServeMux, store StudyStore) {
	mux.HandleFunc("/api/v1/shared/studies/{token}", func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Cache-Control", "private, no-store")
		w.Header().Set("X-Robots-Tag", "noindex, nofollow")
		w.Header().Set("Referrer-Policy", "no-referrer")
		if r.Method != http.MethodGet {
			w.Header().Set("Allow", "GET")
			accessError(w, http.StatusMethodNotAllowed, "READ_ONLY", "Shared studies are read only.")
			return
		}
		token := r.PathValue("token")
		if !bookmarkID.MatchString(token) {
			studyError(w, ErrStudyMissing)
			return
		}
		s, err := store.GetShared(r.Context(), token)
		if err != nil {
			studyError(w, err)
			return
		}
		// Do not expose the private workspace ID or owner/account information.
		s.ID = token
		view, err := studyView(s, r.URL.Query())
		if err != nil {
			studyError(w, err)
			return
		}
		view.Keys = nil
		bookmarkJSON(w, view)
	})
}
