package main

import (
	"crypto/sha256"
	"fmt"
	"strings"
)

func verifyEntombment(b []byte) error {
	if fmt.Sprintf("%x", sha256.Sum256(b)) != "c345942c5a5dee4805fd0142f532cecfff05f337c8e37a8e1264d6f5358047ab" {
		return fmt.Errorf("Entombment reviewed snapshot changed")
	}
	t := athensText(string(b))
	for _, v := range []string{"Theotokopoulos Domenicos (1541 - 1614)", "The Entombment of Christ, ca 1568-1570", "Oil and tempera on panel, 51,5 x 42,9 cm", "Inv. Number Π.9979"} {
		if !strings.Contains(t, v) {
			return fmt.Errorf("Entombment source fact missing: %s", v)
		}
	}
	return nil
}
