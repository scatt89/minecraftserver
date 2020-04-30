# -*- mode: ruby -*-
# vi: set ft=ruby :

Vagrant.configure("2") do |config|
  config.vm.box = "debian/buster64"
  config.ssh.insert_key = false
  config.vm.synced_folder ".", "/vagrant", disabled: true
  config.vm.provider :virtualbox do |v|
    v.memory = 1024
    v.linked_clone = true
  end

  config.vm.define "minecraft" do |minecraft|
    minecraft.vm.hostname = "minecrafttest"
    minecraft.vm.network :private_network, ip: "192.168.60.4"
  end
end