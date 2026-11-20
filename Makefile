TOP := $(dir $(abspath $(firstword $(MAKEFILE_LIST))))
TOOLS_DIR := $(TOP)tools
TWOLITER_DIR := $(TOOLS_DIR)/twoliter
TWOLITER := $(TWOLITER_DIR)/twoliter
CARGO_HOME := $(TOP).cargo

TWOLITER_VERSION ?= "0.25.0"
TWOLITER_SHA256_AARCH64 ?= "04772bbbdfed2d61c90bfc368ecf852e7ed67126e9ad5c9972e70fb464475658"
TWOLITER_SHA256_X86_64 ?= "7d0460cc923555b2af879a47c636b5296d912805b130e82f15808946d1bbf4d4"
KIT ?= bottlerocket-extra-kit
UNAME_ARCH = $(shell uname -m)
ARCH ?= $(UNAME_ARCH)
VENDOR ?= peng
UPSTREAM_SOURCE_FALLBACK ?= false
# Architectures built by build-all-arches, build-and-publish, daily-build and
# release-github. Both are built on the same host; the SDK cross-compiles.
ARCHES ?= x86_64 aarch64

ifeq ($(UNAME_ARCH), aarch64)
	TWOLITER_SHA256=$(TWOLITER_SHA256_AARCH64)
else
	TWOLITER_SHA256=$(TWOLITER_SHA256_X86_64)
endif


export GO_MODULES ?=

all: build

RELEASE_VERSION ?= 1.0.6

# Generate Twoliter.toml. Three modes (mutually exclusive):
#   1. Latest from GitHub (default):
#      make generate-twoliter-toml RELEASE_VERSION=1.0.3
#   2. Copy versions from an existing Twoliter.toml:
#      make generate-twoliter-toml RELEASE_VERSION=1.0.3 TWOLITER_SOURCE=/path/to/Twoliter.toml
#   3. Explicit versions:
#      make generate-twoliter-toml RELEASE_VERSION=1.0.3 CORE_KIT_VERSION=13.0.0 KERNEL_KIT_VERSION=5.0.0 SDK_VERSION=0.70.0
CORE_KIT_VERSION ?=
KERNEL_KIT_VERSION ?=
SDK_VERSION ?=

generate-twoliter-toml:
ifdef TWOLITER_SOURCE
	cd $(TOP)scripts/go && go run ./cmd/generate-twoliter -release $(RELEASE_VERSION) -use-version-from $(TWOLITER_SOURCE) > $(TOP)Twoliter.toml
else
	cd $(TOP)scripts/go && go run ./cmd/generate-twoliter -release $(RELEASE_VERSION) -use-version-latest \
		$(if $(CORE_KIT_VERSION),-core-kit $(CORE_KIT_VERSION)) \
		$(if $(KERNEL_KIT_VERSION),-kernel-kit $(KERNEL_KIT_VERSION)) \
		$(if $(SDK_VERSION),-sdk $(SDK_VERSION)) \
		> $(TOP)Twoliter.toml
endif

prep:
	@mkdir -p $(TWOLITER_DIR)
	@mkdir -p $(CARGO_HOME)
	@$(TOOLS_DIR)/install-twoliter.sh \
		--repo "https://github.com/bottlerocket-os/twoliter" \
		--version v$(TWOLITER_VERSION) \
		--directory $(TWOLITER_DIR) \
		--reuse-existing-install \
		--allow-binary-install $(TWOLITER_SHA256) \
		--allow-from-source

update: prep
	@$(TWOLITER) update

fetch: prep
	@$(TWOLITER) fetch --arch $(ARCH)

build: fetch
ifeq ($(UPSTREAM_SOURCE_FALLBACK),false)
	@$(TWOLITER) build kit $(KIT) --arch $(ARCH)
else
	@$(TWOLITER) build kit $(KIT) --arch $(ARCH) --upstream-source-fallback
endif

# Build the kit once per architecture in ARCHES. publish then pushes every
# archive matching the current commit as a single multi-arch OCI index.
build-all-arches:
	@set -e; for a in $(ARCHES); do \
		echo "==> Building $(KIT) for $$a"; \
		$(MAKE) --no-print-directory build ARCH=$$a; \
	done

publish: prep
	@$(TWOLITER) publish kit $(KIT) $(VENDOR)

build-and-publish: update
	@$(MAKE) --no-print-directory build-all-arches
	@$(MAKE) --no-print-directory publish

# Check for upstream kernel-kit/core-kit/SDK updates and rebuild when any
# version changed. Pass script flags via DAILY_BUILD_ARGS, e.g.:
#   make daily-build DAILY_BUILD_ARGS=--dry-run
#   make daily-build DAILY_BUILD_ARGS=--force
# REGISTRY, PUBLISH_REGIONS, GITHUB_TOKEN, and LOG_FILE are read from the
# environment; see scripts/daily-build.sh --help.
DAILY_BUILD_ARGS ?=

daily-build:
	@VENDOR="$(VENDOR)" RELEASE_VERSION="$(RELEASE_VERSION)" ARCHES="$(ARCHES)" \
		$(TOP)scripts/daily-build.sh $(DAILY_BUILD_ARGS)

# Cut a release: bump release-version, commit, build all ARCHES, publish,
# tag, and create the GitHub release. Pass script flags via RELEASE_ARGS, e.g.:
#   make release-github RELEASE_VERSION=1.0.6
#   make release-github RELEASE_VERSION=1.0.6 RELEASE_ARGS="--latest --draft"
# See scripts/release.sh --help.
RELEASE_ARGS ?=

release-github:
	@if [ "$(origin RELEASE_VERSION)" != "command line" ]; then echo "Error: pass the new version explicitly, e.g. make release-github RELEASE_VERSION=1.0.6"; exit 1; fi
	@VENDOR="$(VENDOR)" ARCHES="$(ARCHES)" \
		$(TOP)scripts/release.sh $(RELEASE_ARGS) $(RELEASE_VERSION)

PACKAGE ?=
export BUILDSYS_UPSTREAM_SOURCE_FALLBACK ?= true

TWOLITER_MAKE = $(TWOLITER) make --cargo-home $(CARGO_HOME) --arch $(ARCH)

# Build a single package: make build-package PACKAGE=awscli2
build-package: prep
	@if [ -z "$(PACKAGE)" ]; then echo "Error: PACKAGE is required, e.g. make build-package PACKAGE=awscli2"; exit 1; fi
	@$(TWOLITER_MAKE) build-package -- PACKAGE=$(PACKAGE)

# Treat any targets after "make twoliter" as arguments to "twoliter make".
ifeq (twoliter,$(firstword $(MAKECMDGOALS)))
  TWOLITER_MAKE_ARGS := $(wordlist 2,$(words $(MAKECMDGOALS)),$(MAKECMDGOALS))
  $(eval $(TWOLITER_MAKE_ARGS):;@:)
endif

# Transform "make twoliter" into "twoliter make", for access to tasks that are
# only available through the embedded Makefile.toml.
twoliter: prep
	@$(TWOLITER_MAKE) $(TWOLITER_MAKE_ARGS)

.PHONY: prep update fetch build build-all-arches publish build-and-publish daily-build release-github twoliter generate-twoliter-toml build-package
