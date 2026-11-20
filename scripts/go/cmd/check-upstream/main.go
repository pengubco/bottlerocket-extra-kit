// check-upstream reports packages whose upstream has a newer release than the
// version in their spec. It is a report, not a gate: it always exits 0 unless
// it cannot run at all.
//
//	go -C scripts/go run ./cmd/check-upstream -root ../..
//
// It understands packages whose [package.metadata.build-package] releases-url
// points at GitHub releases or tags, and the Go toolchain (go.dev/dl). Other
// upstreams are listed as "unchecked". Set GITHUB_TOKEN (or log in with gh)
// to avoid GitHub's 60 requests/hour anonymous limit.
package main

import (
	"encoding/json"
	"flag"
	"fmt"
	"net/http"
	"os"
	"os/exec"
	"path/filepath"
	"regexp"
	"sort"
	"strconv"
	"strings"
	"time"

	"github.com/BurntSushi/toml"
)

var (
	githubRe  = regexp.MustCompile(`^https://github\.com/([^/]+)/([^/]+)/(releases|tags)`)
	versionRe = regexp.MustCompile(`(?m)^Version:\s*(\S+)`)
	numRe     = regexp.MustCompile(`\d+`)
	client    = &http.Client{Timeout: 20 * time.Second}
	token     = githubToken()
)

func githubToken() string {
	if t := os.Getenv("GITHUB_TOKEN"); t != "" {
		return t
	}
	if out, err := exec.Command("gh", "auth", "token").Output(); err == nil {
		return strings.TrimSpace(string(out))
	}
	return ""
}

func getJSON(url string, v any) error {
	req, err := http.NewRequest("GET", url, nil)
	if err != nil {
		return err
	}
	if token != "" && strings.HasPrefix(url, "https://api.github.com/") {
		req.Header.Set("Authorization", "Bearer "+token)
	}
	resp, err := client.Do(req)
	if err != nil {
		return err
	}
	defer resp.Body.Close()
	if resp.StatusCode != http.StatusOK {
		return fmt.Errorf("%s: HTTP %d", url, resp.StatusCode)
	}
	return json.NewDecoder(resp.Body).Decode(v)
}

// latest returns the newest upstream version for a releases-url, or "" if the
// upstream type is not supported.
func latest(releasesURL string) (string, error) {
	if strings.HasPrefix(releasesURL, "https://go.dev/dl") {
		var rel []struct{ Version string }
		if err := getJSON("https://go.dev/dl/?mode=json", &rel); err != nil || len(rel) == 0 {
			return "", err
		}
		return strings.TrimPrefix(rel[0].Version, "go"), nil
	}
	m := githubRe.FindStringSubmatch(releasesURL)
	if m == nil {
		return "", nil
	}
	api := "https://api.github.com/repos/" + m[1] + "/" + m[2]
	if m[3] == "releases" {
		var rel struct {
			TagName string `json:"tag_name"`
		}
		if err := getJSON(api+"/releases/latest", &rel); err == nil {
			return rel.TagName, nil
		}
	}
	var tags []struct{ Name string }
	if err := getJSON(api+"/tags?per_page=100", &tags); err != nil {
		return "", err
	}
	best := ""
	for _, t := range tags {
		if numRe.MatchString(t.Name) && !strings.ContainsAny(t.Name, "-") && newer(t.Name, best) {
			best = t.Name
		}
	}
	return best, nil
}

// normalize strips the tag decorations used by upstreams (v1.2, iotop-1.2,
// release-1.2) down to the dotted number.
func normalize(v string) string {
	if i := strings.IndexAny(v, "0123456789"); i >= 0 {
		v = v[i:]
	}
	return v
}

// newer reports whether version a sorts after b, comparing numeric fields.
func newer(a, b string) bool {
	if b == "" {
		return true
	}
	na, nb := numRe.FindAllString(normalize(a), -1), numRe.FindAllString(normalize(b), -1)
	for i := 0; i < len(na) && i < len(nb); i++ {
		x, _ := strconv.Atoi(na[i])
		y, _ := strconv.Atoi(nb[i])
		if x != y {
			return x > y
		}
	}
	return len(na) > len(nb)
}

func main() {
	root := flag.String("root", ".", "repository root")
	flag.Parse()
	manifests, err := filepath.Glob(filepath.Join(*root, "packages", "*", "Cargo.toml"))
	if err != nil || len(manifests) == 0 {
		fmt.Fprintln(os.Stderr, "no packages found under", *root)
		os.Exit(2)
	}
	sort.Strings(manifests)

	var outdated, current, unchecked []string
	for _, m := range manifests {
		name := filepath.Base(filepath.Dir(m))
		var meta struct {
			Package struct {
				Metadata struct {
					BuildPackage struct {
						ReleasesURL string `toml:"releases-url"`
					} `toml:"build-package"`
				}
			}
		}
		if _, err := toml.DecodeFile(m, &meta); err != nil {
			unchecked = append(unchecked, fmt.Sprintf("%s (%v)", name, err))
			continue
		}
		url := meta.Package.Metadata.BuildPackage.ReleasesURL
		specs, _ := filepath.Glob(filepath.Join(filepath.Dir(m), "*.spec"))
		have := ""
		if len(specs) > 0 {
			data, _ := os.ReadFile(specs[0])
			if v := versionRe.FindSubmatch(data); v != nil {
				have = string(v[1])
			}
		}
		want, err := latest(url)
		switch {
		case err != nil:
			unchecked = append(unchecked, fmt.Sprintf("%s (%v)", name, err))
		case want == "" || have == "" || strings.Contains(have, "%"):
			unchecked = append(unchecked, name)
		case newer(want, have):
			outdated = append(outdated, fmt.Sprintf("%-14s %-12s -> %s", name, have, normalize(want)))
		default:
			current = append(current, name)
		}
	}

	fmt.Printf("Newer upstream release available (%d):\n", len(outdated))
	for _, o := range outdated {
		fmt.Println("  " + o)
	}
	fmt.Printf("Up to date (%d): %s\n", len(current), strings.Join(current, ", "))
	fmt.Printf("Unchecked (%d): %s\n", len(unchecked), strings.Join(unchecked, ", "))
}
