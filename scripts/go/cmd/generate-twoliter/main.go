package main

import (
	"encoding/json"
	"flag"
	"fmt"
	"io"
	"net/http"
	"os"
	"strings"
)

// GitHubRelease represents the structure of a GitHub release API response
type GitHubRelease struct {
	TagName string `json:"tag_name"`
}

// GitHubTag represents the structure of a GitHub tag API response
type GitHubTag struct {
	Name string `json:"name"`
}

// getLatestRelease fetches the latest release version from a GitHub repository
func getLatestRelease(repo string) (string, error) {
	url := fmt.Sprintf("https://api.github.com/repos/%s/releases/latest", repo)

	resp, err := http.Get(url)
	if err != nil {
		return "", fmt.Errorf("failed to fetch release from %s: %w", repo, err)
	}
	defer resp.Body.Close()

	// If releases API returns 404, try tags API as fallback
	if resp.StatusCode == http.StatusNotFound {
		return getLatestTag(repo)
	}

	if resp.StatusCode != http.StatusOK {
		body, _ := io.ReadAll(resp.Body)
		return "", fmt.Errorf("GitHub API returned status %d for %s: %s", resp.StatusCode, repo, string(body))
	}

	var release GitHubRelease
	if err := json.NewDecoder(resp.Body).Decode(&release); err != nil {
		return "", fmt.Errorf("failed to decode release JSON from %s: %w", repo, err)
	}

	// Remove 'v' prefix if present
	version := strings.TrimPrefix(release.TagName, "v")
	return version, nil
}

// getLatestTag fetches the latest tag from a GitHub repository
func getLatestTag(repo string) (string, error) {
	url := fmt.Sprintf("https://api.github.com/repos/%s/tags", repo)

	resp, err := http.Get(url)
	if err != nil {
		return "", fmt.Errorf("failed to fetch tags from %s: %w", repo, err)
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		body, _ := io.ReadAll(resp.Body)
		return "", fmt.Errorf("GitHub API returned status %d for %s tags: %s", resp.StatusCode, repo, string(body))
	}

	var tags []GitHubTag
	if err := json.NewDecoder(resp.Body).Decode(&tags); err != nil {
		return "", fmt.Errorf("failed to decode tags JSON from %s: %w", repo, err)
	}

	if len(tags) == 0 {
		return "", fmt.Errorf("no tags found for %s", repo)
	}

	// Get the first (latest) tag
	// Remove 'v' prefix if present
	version := strings.TrimPrefix(tags[0].Name, "v")
	return version, nil
}

// getVersion returns the provided version or fetches the latest release if version is empty
func getVersion(version, repo string) (string, error) {
	if version != "" {
		return version, nil
	}
	return getLatestRelease(repo)
}

func main() {
	// Define command-line flags
	var releaseVersion string
	var coreKitVersion string
	var kernelKitVersion string
	var sdkVersion string

	flag.StringVar(&releaseVersion, "release", "", "Release version number (required)")
	flag.StringVar(&coreKitVersion, "core-kit", "", "Version of bottlerocket-core-kit (if not provided, fetches latest release)")
	flag.StringVar(&kernelKitVersion, "kernel-kit", "", "Version of bottlerocket-kernel-kit (if not provided, fetches latest release)")
	flag.StringVar(&sdkVersion, "sdk", "", "Version of bottlerocket-sdk (if not provided, fetches latest release)")

	flag.Parse()

	// Validate required flag
	if releaseVersion == "" {
		fmt.Fprintf(os.Stderr, "Error: -release flag is required\n")
		flag.Usage()
		os.Exit(1)
	}

	// Get versions (either from flags or latest releases)
	coreKit, err := getVersion(coreKitVersion, "bottlerocket-os/bottlerocket-core-kit")
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error getting core-kit version: %v\n", err)
		os.Exit(1)
	}

	kernelKit, err := getVersion(kernelKitVersion, "bottlerocket-os/bottlerocket-kernel-kit")
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error getting kernel-kit version: %v\n", err)
		os.Exit(1)
	}

	sdk, err := getVersion(sdkVersion, "bottlerocket-os/bottlerocket-sdk")
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error getting sdk version: %v\n", err)
		os.Exit(1)
	}

	// Generate release-version string
	fullReleaseVersion := fmt.Sprintf("%s-kernalkit-%s-corekit-%s-sdk-%s", releaseVersion, kernelKit, coreKit, sdk)

	// Generate and output Twoliter.toml
	output := fmt.Sprintf(`schema-version = 1
release-version = "%s"

[vendor.bottlerocket]
registry = "public.ecr.aws/bottlerocket"

[[kit]]
name = "bottlerocket-kernel-kit"
version = "%s"
vendor = "bottlerocket"

[[kit]]
name = "bottlerocket-core-kit"
version = "%s"
vendor = "bottlerocket"

[sdk]
name = "bottlerocket-sdk"
version = "%s"
vendor = "bottlerocket"
`, fullReleaseVersion, kernelKit, coreKit, sdk)

	fmt.Print(output)
}
