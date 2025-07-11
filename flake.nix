{
  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixpkgs-unstable";

    pyproject-nix = {
      url = "github:pyproject-nix/pyproject.nix";
      inputs.nixpkgs.follows = "nixpkgs";
    };

    uv2nix = {
      url = "github:pyproject-nix/uv2nix";
      inputs.pyproject-nix.follows = "pyproject-nix";
      inputs.nixpkgs.follows = "nixpkgs";
    };

    pyproject-build-systems = {
      url = "github:pyproject-nix/build-system-pkgs";
      inputs.pyproject-nix.follows = "pyproject-nix";
      inputs.uv2nix.follows = "uv2nix";
      inputs.nixpkgs.follows = "nixpkgs";
    };
  };

  outputs =
    {
      nixpkgs,
      uv2nix,
      pyproject-nix,
      pyproject-build-systems,
      ...
    }:
    let
      pkgs = import nixpkgs { system = "x86_64-linux"; };
      workspace = uv2nix.lib.workspace.loadWorkspace { workspaceRoot = ./.; };
      overlay = workspace.mkPyprojectOverlay { sourcePreference = "wheel"; };
      pythonSet =
        (pkgs.callPackage pyproject-nix.build.packages {
          python = pkgs.python312;
        }).overrideScope
          (
            pkgs.lib.composeManyExtensions [
              pyproject-build-systems.overlays.default
              overlay
            ]
          );
    in
    {
      devShells."x86_64-linux".default = pkgs.mkShell {
        buildInputs = with pkgs; [
          python3
          uv
          bun
        ];
      };

      packages."x86_64-linux" = rec {
        default = sb_mcp;
        sb_mcp = pythonSet.mkVirtualEnv "sb_mcp" workspace.deps.default;
      };
    };
}
