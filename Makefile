TOP := $(dir $(abspath $(firstword $(MAKEFILE_LIST))))
TOOLS_DIR := $(TOP)tools
TWOLITER_DIR := $(TOOLS_DIR)/twoliter
TWOLITER := $(TWOLITER_DIR)/twoliter
CARGO_HOME := $(TOP).cargo

TWOLITER_VERSION ?= "0.16.0"
TWOLITER_SHA256_AARCH64 ?= "c0586e977c15841eb7f948b9d47a6f798cfa6987d55ba30086b7f04ae3ca5988"
TWOLITER_SHA256_X86_64 ?= "c5f38cd5b93fff04f3cf8f2a614193b243179a790ac98a3e23eb767696e254d4"
KIT ?= bottlerocket-extra-kit
UNAME_ARCH = $(shell uname -m)
ARCH ?= $(UNAME_ARCH)
VENDOR ?= peng
UPSTREAM_SOURCE_FALLBACK ?= false

ifeq ($(UNAME_ARCH), aarch64)
	TWOLITER_SHA256=$(TWOLITER_SHA256_AARCH64)
else
	TWOLITER_SHA256=$(TWOLITER_SHA256_X86_64)
endif


export GO_MODULES = ecs-gpu-init host-ctr

all: build

RELEASE_VERSION ?= 1.0.1

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
ifeq ($(UPSTREAM_SOURCE_FALLBACK), "false")
	@$(TWOLITER) build kit $(KIT) --arch $(ARCH)
else
	@$(TWOLITER) build kit $(KIT) --arch $(ARCH) --upstream-source-fallback
endif

publish: prep
	@$(TWOLITER) publish kit $(KIT) $(VENDOR)

build-and-publish: update fetch build publish

release-github:
	@if [ -z "$(RELEASE_VERSION)" ]; then echo "Error: RELEASE_VERSION is required, e.g. make release-github RELEASE_VERSION=1.0.2"; exit 1; fi
	@$(TOP)scripts/release.sh $(RELEASE_VERSION) $(VENDOR)

TWOLITER_MAKE = $(TWOLITER) make --cargo-home $(CARGO_HOME) --arch $(ARCH)

# Treat any targets after "make twoliter" as arguments to "twoliter make".
ifeq (twoliter,$(firstword $(MAKECMDGOALS)))
  TWOLITER_MAKE_ARGS := $(wordlist 2,$(words $(MAKECMDGOALS)),$(MAKECMDGOALS))
  $(eval $(TWOLITER_MAKE_ARGS):;@:)
endif

# Transform "make twoliter" into "twoliter make", for access to tasks that are
# only available through the embedded Makefile.toml.
twoliter: prep
	@$(TWOLITER_MAKE) $(TWOLITER_MAKE_ARGS)

.PHONY: prep update fetch build publish build-and-publish release-github twoliter generate-twoliter-toml
