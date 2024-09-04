{ pkgs ? import <nixpkgs> {} }:

(pkgs.buildFHSEnv {
  name = "arcpy";
  targetPkgs = pkgs: (with pkgs; [
    unrar
  ]);
  profile = ''
    export UNRAR_LIB_PATH="${pkgs.lib.makeLibraryPath [pkgs.unrar]}/libunrar.so"
  '';
}).env
