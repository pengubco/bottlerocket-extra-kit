package main

import (
	"testing"

	"github.com/BurntSushi/toml"
)

const sample = `
release-version = "1.0.6"

[vendor.peng]
registry = "public.ecr.aws/m8c0s8v8"

[[kit]]
name = "bottlerocket-kernel-kit"
version = "9.8.0"

[[kit]]
name = "bottlerocket-core-kit"
version = "18.1.0"

[sdk]
version = "0.83.0"
`

func TestLookup(t *testing.T) {
	var doc map[string]any
	if _, err := toml.Decode(sample, &doc); err != nil {
		t.Fatal(err)
	}
	cases := []struct{ path, want string }{
		{"release-version", "1.0.6"},
		{"sdk.version", "0.83.0"},
		{"vendor.peng.registry", "public.ecr.aws/m8c0s8v8"},
		{"kit[name=bottlerocket-core-kit].version", "18.1.0"},
		{"kit[name=bottlerocket-kernel-kit].version", "9.8.0"},
	}
	for _, c := range cases {
		got, err := lookup(doc, c.path)
		if err != nil || got != c.want {
			t.Errorf("lookup(%q) = %v, %v; want %q", c.path, got, err, c.want)
		}
	}
	for _, path := range []string{"missing", "sdk.missing", "kit[name=nope].version", "release-version.x"} {
		if _, err := lookup(doc, path); err == nil {
			t.Errorf("lookup(%q) succeeded; want error", path)
		}
	}
}
