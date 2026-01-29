{
  description = "Talent Match AI";

  inputs = {
    nixpkgs.url = "github:nixos/nixpkgs/nixos-unstable";
  };

  outputs =
    { nixpkgs, ... }:
    let
      inherit (nixpkgs) lib;
      forAllSystems = lib.genAttrs lib.systems.flakeExposed;
    in
    {
      devShells = forAllSystems (
        system:
        let
          pkgs = nixpkgs.legacyPackages.${system};

          # Native dependencies for WeasyPrint
          weasyLibs = [
            pkgs.cairo
            pkgs.pango
            pkgs.gdk-pixbuf
            pkgs.harfbuzz
            pkgs.freetype
            pkgs.libffi
            pkgs.libjpeg
            pkgs.fontconfig
          ];

          # Manylinux-compatible runtime set (useful for binary wheels)
          manylinuxLibs = pkgs.pythonManylinuxPackages.manylinux1;
        in
        {
          default = pkgs.mkShell {
            packages = [
              pkgs.python312
              pkgs.uv
            ];

            env = lib.optionalAttrs pkgs.stdenv.isLinux {
              LD_LIBRARY_PATH = lib.makeLibraryPath (weasyLibs ++ manylinuxLibs);
            };

            shellHook = ''
              export PYTHONPATH="src"
              cd backend
              uv sync --group dev
              . .venv/bin/activate
              [[ -f .env ]] && set -a && source .env && set +a
              [[ $DEVSHELL_SHELL ]] && exec "$DEVSHELL_SHELL"
            '';
          };

          client = pkgs.mkShell {
            packages = [
              pkgs.python312
              pkgs.uv
            ];

            env = lib.optionalAttrs pkgs.stdenv.isLinux {
              LD_LIBRARY_PATH = lib.makeLibraryPath (manylinuxLibs);
            };

            shellHook = ''
              cd client
              uv sync
              . .venv/bin/activate
              [[ -f .env ]] && set -a && source .env && set +a
              [[ $DEVSHELL_SHELL ]] && exec "$DEVSHELL_SHELL"
            '';
          };
        }
      );
    };
}
