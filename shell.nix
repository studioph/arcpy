{ pkgs ? import <nixpkgs> {} }:

(pkgs.buildFHSEnv {
  name = "arcpy";
  targetPkgs = pkgs: (with pkgs; [
    unrar
  ]);
}).env
