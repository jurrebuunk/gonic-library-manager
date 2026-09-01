{
  description = "Development shell and runnable package for Gonic Library Manager";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
  };

  outputs = { self, nixpkgs }:
    let
      systems = [ "x86_64-linux" "aarch64-linux" ];
      forAllSystems = nixpkgs.lib.genAttrs systems;
      pythonFor = pkgs: pkgs.python312.override {
        packageOverrides = _pyFinal: pyPrev: {
          # Nixpkgs currently runs an upstream inline-snapshot test suite that is
          # flaky/failing on this channel while building FastAPI's dependency tree.
          # We only need it as a transitive runtime dependency, not for its tests.
          inline-snapshot = pyPrev.inline-snapshot.overridePythonAttrs (_old: {
            doCheck = false;
          });
        };
      };
    in
    {
      packages = forAllSystems (system:
        let
          pkgs = import nixpkgs { inherit system; };
          pythonEnv = (pythonFor pkgs).withPackages (ps: with ps; [
            fastapi
            jinja2
            mutagen
            python-multipart
            uvicorn
          ]);
        in
        {
          default = pkgs.writeShellApplication {
            name = "gonic-library-manager";
            runtimeInputs = [ pythonEnv ];
            text = ''
              export MUSIC_LIBRARY_PATH="''${MUSIC_LIBRARY_PATH:-$PWD/example-music}"
              export DATA_DIR="''${DATA_DIR:-$PWD/data}"
              mkdir -p "$MUSIC_LIBRARY_PATH" "$DATA_DIR"

              exec uvicorn gonic_library_manager.main:app \
                --app-dir "${self}/app" \
                --host "''${APP_HOST:-127.0.0.1}" \
                --port "''${APP_PORT:-8080}"
            '';
          };
        });

      devShells = forAllSystems (system:
        let
          pkgs = import nixpkgs { inherit system; };
          pythonEnv = (pythonFor pkgs).withPackages (ps: with ps; [
            fastapi
            httpx
            jinja2
            mutagen
            python-multipart
            uvicorn
          ]);
        in
        {
          default = pkgs.mkShell {
            packages = [
              pythonEnv
              pkgs.docker-compose
              pkgs.ffmpeg
              pkgs.git
              pkgs.ruff
              pkgs.sqlite
              pkgs.yt-dlp
            ];

            shellHook = ''
              export PYTHONPATH="$PWD/app''${PYTHONPATH:+:$PYTHONPATH}"
              export MUSIC_LIBRARY_PATH="''${MUSIC_LIBRARY_PATH:-$PWD/example-music}"
              export DATA_DIR="''${DATA_DIR:-$PWD/data}"
              mkdir -p "$MUSIC_LIBRARY_PATH" "$DATA_DIR"

              echo "Gonic Library Manager dev shell"
              echo "  Run app:   uvicorn gonic_library_manager.main:app --reload --app-dir app --host 127.0.0.1 --port 8080"
              echo "  Run tests: python -m unittest discover -s tests -v"
              echo "  Music:     $MUSIC_LIBRARY_PATH"
              echo "  Data:      $DATA_DIR"
            '';
          };
        });

      checks = forAllSystems (system:
        let
          pkgs = import nixpkgs { inherit system; };
          pythonEnv = (pythonFor pkgs).withPackages (ps: with ps; [
            fastapi
            jinja2
            mutagen
            python-multipart
            uvicorn
          ]);
        in
        {
          unit-tests = pkgs.runCommand "gonic-library-manager-tests" { } ''
            cp -r ${self} source
            chmod -R u+w source
            cd source
            export PYTHONPATH=$PWD/app
            export MUSIC_LIBRARY_PATH=$TMPDIR/music
            export DATA_DIR=$TMPDIR/data
            ${pythonEnv}/bin/python -m unittest discover -s tests -v
            touch $out
          '';
        });
    };
}
