{
  description = "Galadril Dev Env";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    rust-overlay = {
      url = "github:oxalica/rust-overlay";
      inputs.nixpkgs.follows = "nixpkgs";
    };
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs =
    {
      self,
      nixpkgs,
      rust-overlay,
      flake-utils,
      ...
    }:
    flake-utils.lib.eachDefaultSystem (
      system:
      let
        overlays = [ (import rust-overlay) ];
        pkgs = import nixpkgs { inherit system overlays; };
      in
      {
        devShells.default = pkgs.mkShell {
          nativeBuildInputs = with pkgs; [
            bazelisk
            uv
            rust-bin.stable.latest.default
            python3
            podman
            podman-compose
            nixfmt
          ];

          # Make sure XCode is installed on your device.
          shellHook = ''
            export DEVELOPER_DIR="/Applications/Xcode.app/Contents/Developer"
            export SDKROOT=$(xcrun --show-sdk-path)
            export CC=/usr/bin/clang
            export CXX=/usr/bin/clang++
          '';
        };
      }
    )
    // {
      nixosConfigurations.server = nixpkgs.lib.nixosSystem {
        system = "x86_64-linux";
        specialArgs = { inherit self; };
        modules = [
          ./nix-server/configuration.nix
        ];
      };
    };
}
