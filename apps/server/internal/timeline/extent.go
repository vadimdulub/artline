package timeline

// DateExtent describes all dated matches before pagination, inside the requested
// interval. It never derives chronology from the currently loaded page.
type DateExtent struct {
	Start int `json:"start"`
	End   int `json:"end"`
}

func FitExtent(start, end *int, minimum, maximum int) *DateExtent {
	if start == nil || end == nil || minimum >= maximum {
		return nil
	}
	a, b := max(*start, minimum), min(*end, maximum)
	if a > b || a == 0 || b == 0 {
		return nil
	}
	if a == b {
		if b < maximum {
			b++
			if b == 0 {
				b++
			}
		} else {
			a--
			if a == 0 {
				a--
			}
		}
	}
	return &DateExtent{a, b}
}

func MergeExtents(a, b *DateExtent) *DateExtent {
	if a == nil {
		return b
	}
	if b == nil {
		return a
	}
	return &DateExtent{min(a.Start, b.Start), max(a.End, b.End)}
}
