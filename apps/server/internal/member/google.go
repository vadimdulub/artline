package member

import (
	"context"
	"crypto/subtle"
	"errors"
	"net/http"
	"time"

	"github.com/coreos/go-oidc/v3/oidc"
	"golang.org/x/oauth2"
)

type Google interface {
	AuthURL(state, nonce, verifier string) string
	Exchange(context.Context, string, string, string) (Identity, error)
}

type googleClient struct {
	oauth    oauth2.Config
	verifier *oidc.IDTokenVerifier
	client   *http.Client
}

func newGoogle(clientID, secret, origin string) Google {
	client := &http.Client{Timeout: 10 * time.Second}
	ctx := oidc.ClientContext(context.Background(), client)
	return &googleClient{
		oauth: oauth2.Config{ClientID: clientID, ClientSecret: secret, RedirectURL: origin + "/api/auth/google/callback",
			Scopes:   []string{oidc.ScopeOpenID, "email", "profile"},
			Endpoint: oauth2.Endpoint{AuthURL: "https://accounts.google.com/o/oauth2/v2/auth", TokenURL: "https://oauth2.googleapis.com/token", AuthStyle: oauth2.AuthStyleInParams}},
		verifier: oidc.NewVerifier("https://accounts.google.com", oidc.NewRemoteKeySet(ctx, "https://www.googleapis.com/oauth2/v3/certs"), &oidc.Config{ClientID: clientID}),
		client:   client,
	}
}

func (g *googleClient) AuthURL(state, nonce, verifier string) string {
	return g.oauth.AuthCodeURL(state, oidc.Nonce(nonce), oauth2.S256ChallengeOption(verifier), oauth2.SetAuthURLParam("prompt", "select_account"))
}

func (g *googleClient) Exchange(ctx context.Context, code, verifier, nonce string) (Identity, error) {
	ctx = context.WithValue(ctx, oauth2.HTTPClient, g.client)
	token, err := g.oauth.Exchange(ctx, code, oauth2.VerifierOption(verifier))
	if err != nil {
		return Identity{}, err
	}
	raw, ok := token.Extra("id_token").(string)
	if !ok {
		return Identity{}, errors.New("missing ID token")
	}
	id, err := g.verifier.Verify(ctx, raw)
	if err != nil {
		return Identity{}, err
	}
	var claims struct {
		Email           string `json:"email"`
		Verified        bool   `json:"email_verified"`
		Name            string `json:"name"`
		AuthorizedParty string `json:"azp"`
	}
	if err = id.Claims(&claims); err != nil {
		return Identity{}, err
	}
	if id.Subject == "" || claims.Email == "" || !claims.Verified || subtle.ConstantTimeCompare([]byte(id.Nonce), []byte(nonce)) != 1 || (claims.AuthorizedParty != "" && claims.AuthorizedParty != g.oauth.ClientID) {
		return Identity{}, errors.New("invalid identity claims")
	}
	return Identity{Subject: id.Subject, Email: claims.Email, Name: claims.Name}, nil
}
