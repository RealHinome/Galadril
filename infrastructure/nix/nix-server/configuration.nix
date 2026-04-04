{
  config,
  pkgs,
  self,
  ...
}:

{
  virtualisation.podman = {
    enable = true;
    dockerCompat = true;
    defaultNetwork.settings.dns_enabled = true;
  };

  environment.systemPackages = with pkgs; [
    podman-compose
  ];

  systemd.services.galadril-containers = {
    description = "OCI Galadril";
    wantedBy = [ "multi-user.target" ];
    after = [
      "network.target"
      "podman.socket"
    ];

    serviceConfig = {
      Type = "oneshot";
      RemainAfterExit = true;
      WorkingDirectory = "${self}/../docker";
      ExecStart = "${pkgs.podman-compose}/bin/podman-compose -p galadril up -d";
      ExecStop = "${pkgs.podman-compose}/bin/podman-compose -p galadril down";
    };
  };

  networking.firewall.enable = true;
  system.stateVersion = "23.11";
}
