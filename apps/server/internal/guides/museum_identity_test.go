package guides

import (
	"net/url"
	"testing"
)

func TestDresdenGuideMuseumIdentity(t *testing.T) {
	page, err := Default.Search(url.Values{"institution": {"museum-source-70210fb9f16ace3d158a"}})
	if err != nil || page.Matched != 1 || len(page.Items) != 1 || page.Items[0].Slug != "old-masters-dresden" {
		t.Fatalf("Dresden association: %+v %v", page, err)
	}
	page, err = Default.Search(url.Values{"institution": {"wikimedia-museum-q1501219"}})
	if err != nil {
		t.Fatal(err)
	}
	for _, entry := range page.Items {
		if entry.Slug == "old-masters-dresden" {
			t.Fatal("Dresden guide still linked to Kassel")
		}
	}
}
