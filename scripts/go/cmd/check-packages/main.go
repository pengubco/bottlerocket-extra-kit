// check-packages verifies that every package under packages/ is wired into the
// kit and documented consistently. Run it from the repository root:
//
//	go -C scripts/go run ./cmd/check-packages -root ../..
//
// For each packages/<name>/Cargo.toml it checks that:
//   - the kit's Cargo.toml lists <name> under [build-dependencies];
//   - Cargo.lock has an entry for <name>;
//   - the README "## Packages" list has a "- [<name>]" bullet;
//   - a "vX.Y.Z" in that bullet matches the spec's Version (macros from
//     %global/%define are expanded);
//
// and that the README bullets are sorted and have no entries for packages
// that don't exist. It prints every problem and exits 1 if there were any.
package main

import (
	"bufio"
	"flag"
	"fmt"
	"os"
	"path/filepath"
	"regexp"
	"sort"
	"strings"

	"github.com/BurntSushi/toml"
)

var (
	bulletRe  = regexp.MustCompile(`^- \[([^\]]+)\](?:\([^)]*\))?\s*(?:v(\S+))?`)
	globalRe  = regexp.MustCompile(`^%(?:global|define)\s+(\S+)\s+(\S+)`)
	versionRe = regexp.MustCompile(`^Version:\s*(\S+)`)
	macroRe   = regexp.MustCompile(`%\{\??([A-Za-z0-9_]+)\}`)
)

type bullet struct {
	name, version string
}

// readmeBullets returns the bullets of the "## Packages" section, in order.
func readmeBullets(path string) ([]bullet, error) {
	f, err := os.Open(path)
	if err != nil {
		return nil, err
	}
	defer f.Close()
	var out []bullet
	in := false
	s := bufio.NewScanner(f)
	s.Buffer(make([]byte, 1<<20), 1<<20)
	for s.Scan() {
		line := s.Text()
		if strings.HasPrefix(line, "## ") {
			in = strings.TrimSpace(line) == "## Packages"
			continue
		}
		if m := bulletRe.FindStringSubmatch(line); in && m != nil {
			out = append(out, bullet{m[1], strings.TrimRight(m[2], ".,;:")})
		}
	}
	return out, s.Err()
}

// specVersion returns the expanded Version: of a spec, or "" if it can't be
// fully expanded.
func specVersion(path string) (string, error) {
	data, err := os.ReadFile(path)
	if err != nil {
		return "", err
	}
	macros := map[string]string{}
	version := ""
	for _, line := range strings.Split(string(data), "\n") {
		if m := globalRe.FindStringSubmatch(line); m != nil {
			macros[m[1]] = m[2]
		}
		if m := versionRe.FindStringSubmatch(line); m != nil && version == "" {
			version = m[1]
		}
	}
	for i := 0; i < 5 && strings.Contains(version, "%"); i++ {
		version = macroRe.ReplaceAllStringFunc(version, func(s string) string {
			if v, ok := macros[macroRe.FindStringSubmatch(s)[1]]; ok {
				return v
			}
			return s
		})
	}
	if strings.Contains(version, "%") {
		return "", nil
	}
	return version, nil
}

func check(root string) []string {
	var problems []string
	add := func(format string, args ...any) { problems = append(problems, fmt.Sprintf(format, args...)) }

	manifests, _ := filepath.Glob(filepath.Join(root, "packages", "*", "Cargo.toml"))
	var pkgs []string
	for _, m := range manifests {
		pkgs = append(pkgs, filepath.Base(filepath.Dir(m)))
	}
	sort.Strings(pkgs)

	var kit struct {
		BuildDeps map[string]any `toml:"build-dependencies"`
	}
	kitPath := filepath.Join(root, "kits", "bottlerocket-extra-kit", "Cargo.toml")
	if _, err := toml.DecodeFile(kitPath, &kit); err != nil {
		return []string{fmt.Sprintf("%s: %v", kitPath, err)}
	}

	var lock struct {
		Package []struct{ Name string } `toml:"package"`
	}
	if _, err := toml.DecodeFile(filepath.Join(root, "Cargo.lock"), &lock); err != nil {
		return []string{fmt.Sprintf("Cargo.lock: %v", err)}
	}
	locked := map[string]bool{}
	for _, p := range lock.Package {
		locked[p.Name] = true
	}

	bullets, err := readmeBullets(filepath.Join(root, "README.md"))
	if err != nil {
		return []string{fmt.Sprintf("README.md: %v", err)}
	}
	documented := map[string]bullet{}
	var names []string
	for _, b := range bullets {
		documented[b.name] = b
		names = append(names, b.name)
	}
	if !sort.StringsAreSorted(names) {
		add("README.md: the \"## Packages\" bullets are not in alphabetical order")
	}

	known := map[string]bool{}
	for _, p := range pkgs {
		known[p] = true
		if _, ok := kit.BuildDeps[p]; !ok {
			add("%s: not listed in [build-dependencies] of %s", p, kitPath)
		}
		if !locked[p] {
			add("%s: missing from Cargo.lock (run cargo generate-lockfile --offline)", p)
		}
		b, ok := documented[p]
		if !ok {
			add("%s: no \"- [%s]\" bullet in README.md \"## Packages\"", p, p)
			continue
		}
		specs, _ := filepath.Glob(filepath.Join(root, "packages", p, "*.spec"))
		if b.version == "" || len(specs) == 0 {
			continue
		}
		v, err := specVersion(specs[0])
		if err != nil {
			add("%s: %v", p, err)
		} else if v != "" && v != b.version {
			add("%s: README says v%s but %s has Version %s", p, b.version, filepath.Base(specs[0]), v)
		}
	}
	for _, n := range names {
		if !known[n] {
			add("README.md: bullet for %q, but there is no packages/%s", n, n)
		}
	}
	for dep := range kit.BuildDeps {
		if !known[dep] {
			add("%s: build-dependency %q has no packages/%s", kitPath, dep, dep)
		}
	}
	return problems
}

func main() {
	root := flag.String("root", ".", "repository root")
	flag.Parse()
	problems := check(*root)
	for _, p := range problems {
		fmt.Println(p)
	}
	if len(problems) > 0 {
		os.Exit(1)
	}
	fmt.Println("all packages are consistent")
}
