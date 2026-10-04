package member

import (
	"context"
	"crypto"
	"crypto/rand"
	"crypto/rsa"
	"crypto/sha256"
	"encoding/base64"
	"encoding/json"
	"math/big"
	"net/http"
	"net/http/httptest"
	"strings"
	"testing"
	"time"

	"github.com/coreos/go-oidc/v3/oidc"
)

func TestGoogleRejectsInvalidSignedIdentities(t *testing.T) {
	key, err := rsa.GenerateKey(rand.Reader, 2048)
	if err != nil {
		t.Fatal(err)
	}
	for _, kind := range []string{"valid", "issuer", "audience", "expired", "nonce", "unverified", "no-subject", "no-email", "authorized-party", "signature"} {
		t.Run(kind, func(t *testing.T) {
			claims := map[string]any{"iss": "https://accounts.google.com", "aud": "client", "sub": "google-123", "exp": time.Now().Add(time.Hour).Unix(), "iat": time.Now().Unix(), "nonce": "nonce", "email": "reader@example.org", "email_verified": true, "name": "Reader", "azp": "client"}
			switch kind {
			case "issuer":
				claims["iss"] = "https://evil.example"
			case "audience":
				claims["aud"] = "other-client"
			case "expired":
				claims["exp"] = time.Now().Add(-time.Hour).Unix()
			case "nonce":
				claims["nonce"] = "other-flow"
			case "unverified":
				claims["email_verified"] = false
			case "no-subject":
				delete(claims, "sub")
			case "no-email":
				delete(claims, "email")
			case "authorized-party":
				claims["azp"] = "other-client"
			}
			body, _ := json.Marshal(claims)
			header := base64.RawURLEncoding.EncodeToString([]byte(`{"alg":"RS256","kid":"test-key"}`))
			payload := header + "." + base64.RawURLEncoding.EncodeToString(body)
			digest := sha256.Sum256([]byte(payload))
			sig, err := rsa.SignPKCS1v15(rand.Reader, key, crypto.SHA256, digest[:])
			if err != nil {
				t.Fatal(err)
			}
			if kind == "signature" {
				sig[0] ^= 0xff
			}
			raw := payload + "." + base64.RawURLEncoding.EncodeToString(sig)
			server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
				w.Header().Set("Content-Type", "application/json")
				if r.URL.Path == "/keys" {
					json.NewEncoder(w).Encode(map[string]any{"keys": []any{map[string]string{"kty": "RSA", "kid": "test-key", "alg": "RS256", "use": "sig", "n": base64.RawURLEncoding.EncodeToString(key.N.Bytes()), "e": base64.RawURLEncoding.EncodeToString(big.NewInt(int64(key.E)).Bytes())}}})
				} else {
					r.ParseForm()
					if r.Form.Get("code_verifier") != strings.Repeat("v", 43) || r.Form.Get("redirect_uri") != "https://artlines.org/api/auth/google/callback" {
						t.Error("missing PKCE or incorrect redirect")
					}
					json.NewEncoder(w).Encode(map[string]any{"access_token": "unused", "token_type": "Bearer", "id_token": raw})
				}
			}))
			defer server.Close()
			g := newGoogle("client", "secret", "https://artlines.org").(*googleClient)
			g.oauth.Endpoint.TokenURL = server.URL + "/token"
			g.verifier = oidc.NewVerifier("https://accounts.google.com", oidc.NewRemoteKeySet(context.Background(), server.URL+"/keys"), &oidc.Config{ClientID: "client"})
			identity, err := g.Exchange(context.Background(), "code", strings.Repeat("v", 43), "nonce")
			if kind == "valid" {
				if err != nil || identity.Subject != "google-123" {
					t.Fatalf("valid identity: %v", err)
				}
			} else if err == nil {
				t.Fatal("invalid token accepted")
			}
		})
	}
}
