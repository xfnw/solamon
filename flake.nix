{
  inputs.nixpkgs.url = "github:NixOS/nixpkgs/nixpkgs-unstable";

  outputs = { nixpkgs, ... }: let
    forAllSystems = p: nixpkgs.lib.genAttrs [
      "aarch64-darwin"
      "aarch64-linux"
      "x86_64-linux"
    ] (system: p nixpkgs.legacyPackages.${system});
  in {
    packages = forAllSystems (pkgs: let
      pp = pkgs.python3Packages;
      anyio = pp.anyio.overridePythonAttrs (old: rec {
        version = "2.0.2";
        doCheck = false; # annoyingly slow
        src = pkgs.fetchFromGitHub {
          owner = "agronholm";
          repo = "anyio";
          rev = "refs/tags/${version}";
          hash = "sha256-u0/6hrsS/vGxfSK/oc3ou+O6EeXJ6nfpuJRpUbP7yho=";
        };
      });
      ircrobots = pp.ircrobots.override { inherit anyio; };
    in {
      default = pkgs.writers.writePython3Bin "solamon" {
        libraries = [ pp.aiohttp ircrobots ];
        flakeIgnore = [ "E265" "E401" "E501" "W503" ];
      } ./solamon.py;
    });
  };
}
