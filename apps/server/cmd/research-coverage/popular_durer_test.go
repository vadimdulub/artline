package main

import (
 "os"
 "path/filepath"
 "strings"
 "testing"
)

func TestDurerPinnedMuseumFacts(t *testing.T) {
 for _,f:=range durerFacts { t.Run(f.Acc,func(t *testing.T) {
  path:=filepath.Join("../../../..","content/imports/popular-europe-session-20260911/durer/durer-"+f.ID+".html")
  b,err:=os.ReadFile(path); if os.IsNotExist(err) { t.Skip("private research capture absent") }; if err!=nil { t.Fatal(err) }
  if _,err=durerFields(string(b),f); err!=nil { t.Fatal(err) }
  for _,bad:=range []string{
   strings.ReplaceAll(string(b),"Albrecht Dürer","Albrecht Dürer (Kopie nach)"),
   strings.ReplaceAll(string(b),"Bestand","Different collection"),
   strings.ReplaceAll(string(b),"https://creativecommons.org/licenses/by-sa/4.0/","https://example.com/copyright"),
   strings.ReplaceAll(string(b),"Inventarnummer","Other number"),
  } { if _,err=durerFields(bad,f); err==nil { t.Fatal("unsafe museum facts accepted") } }
 }) }
}
