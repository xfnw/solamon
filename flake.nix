{
  inputs.nixpkgs.url = "github:NixOS/nixpkgs/nixpkgs-unstable";

  outputs = { nixpkgs, ... }: let
    forAllSystems = p: nixpkgs.lib.genAttrs [
      "aarch64-darwin"
      "aarch64-linux"
      "x86_64-linux"
    ] (system: p nixpkgs.legacyPackages.${system});
  in {
    packages = forAllSystems (pkgs: {
      default = pkgs.writers.writePython3Bin "solamon" {
        libraries = with pkgs.python3Packages; [ aiohttp ircrobots ];
        flakeIgnore = [ "E265" "E401" "E501" "W503" ];
      } ./solamon.py;
    });
  };
}
