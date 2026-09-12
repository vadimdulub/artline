package main

import "testing"

func TestCaenCompoundNamesAreNotCollaborators(t *testing.T) {
 a:=knownAuthor{QID:"Q9440",Name:"Paolo Veronese"}
 index:=map[string][]knownAuthor{authorityKey("VERONESE"):{a},authorityKey("CALIARI Paolo"):{a},authorityKey("Other"):{knownAuthor{QID:"Q1"}}}
 if got,ok:=caenAuthor("VERONESE (dit);CALIARI Paolo;(peintre)",index); !ok || got.QID!=a.QID { t.Fatal("exact documented aliases not resolved") }
 for _,bad:=range []string{"VERONESE (d'après);CALIARI Paolo", "VERONESE;Other", "VERONESE (atelier de)", "CALIARI", "VERONESE;Unknown"} {
  if _,ok:=caenAuthor(bad,index); ok { t.Errorf("unsafe creator accepted: %s",bad) }
 }
}
