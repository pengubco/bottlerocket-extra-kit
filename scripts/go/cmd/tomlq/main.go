// tomlq prints one value from a TOML file, for use from shell scripts.
//
// Usage: tomlq -f FILE PATH
//
// PATH is a dot-separated key path. An array of tables is indexed by a field
// match written as key[field=value]. Examples:
//
//	tomlq -f Twoliter.toml release-version
//	tomlq -f Twoliter.toml sdk.version
//	tomlq -f Twoliter.toml 'kit[name=bottlerocket-core-kit].version'
//	tomlq -f Infra.toml vendor.peng.registry
//
// It exits 1 if the path does not exist and 2 on usage or parse errors.
package main

import (
	"flag"
	"fmt"
	"os"
	"regexp"
	"strings"

	"github.com/BurntSushi/toml"
)

var selector = regexp.MustCompile(`^([^\[\]]+)\[([^=\]]+)=([^\]]*)\]$`)

// lookup walks doc along path and returns the value it finds.
func lookup(doc map[string]any, path string) (any, error) {
	var cur any = doc
	for _, part := range strings.Split(path, ".") {
		key, field, want, isSel := part, "", "", false
		if m := selector.FindStringSubmatch(part); m != nil {
			key, field, want, isSel = m[1], m[2], m[3], true
		}
		table, ok := cur.(map[string]any)
		if !ok {
			return nil, fmt.Errorf("%q: parent is not a table", part)
		}
		next, ok := table[key]
		if !ok {
			return nil, fmt.Errorf("%q: key not found", key)
		}
		if isSel {
			found := false
			if arr, ok := next.([]map[string]any); ok {
				for _, t := range arr {
					if fmt.Sprint(t[field]) == want {
						next, found = t, true
						break
					}
				}
			}
			if !found {
				return nil, fmt.Errorf("%q: no entry with %s=%s", key, field, want)
			}
		}
		cur = next
	}
	return cur, nil
}

func main() {
	file := flag.String("f", "", "TOML file to read (required)")
	flag.Parse()
	if *file == "" || flag.NArg() != 1 {
		fmt.Fprintln(os.Stderr, "usage: tomlq -f FILE PATH")
		os.Exit(2)
	}
	var doc map[string]any
	if _, err := toml.DecodeFile(*file, &doc); err != nil {
		fmt.Fprintf(os.Stderr, "tomlq: %v\n", err)
		os.Exit(2)
	}
	v, err := lookup(doc, flag.Arg(0))
	if err != nil {
		fmt.Fprintf(os.Stderr, "tomlq: %s: %v\n", *file, err)
		os.Exit(1)
	}
	switch v.(type) {
	case map[string]any, []map[string]any:
		fmt.Fprintf(os.Stderr, "tomlq: %s is a table, not a value\n", flag.Arg(0))
		os.Exit(1)
	}
	fmt.Println(v)
}
