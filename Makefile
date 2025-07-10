TOP := $(dir $(abspath $(firstword $(MAKEFILE_LIST))))
TOOLS_DIR := $(TOP)tools
TWOLITER_DIR := $(TOOLS_DIR)/twoliter
TWOLITER := $(TWOLITER_DIR)/twoliter
CARGO_HOME := $(TOP).cargo

TWOLITER_VERSION ?= "0.8.1"
TWOLITER_SHA256_AARCH64 ?= "b3df355b5732884bf5e311709bc9a0d0a34ade97c1d7c4cf101cbce4e766de33"
TWOLITER_SHA256_X86_64 ?= "cc83689a878f77c1110ca08fb52b23ce5e0cdbe1b38ff074e913e0ebe5be93f9"
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

.PHONY: prep update fetch build publish twoliter
