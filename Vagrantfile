# -*- mode: ruby -*-
# vi: set ft=ruby :

Vagrant.configure("2") do |config|
  config.ssh.insert_key = false
  
  config.vm.define "compute" do |node|
    node.vm.box = "almalinux/8"
  #  node.vm.box_version = "5.0.0"
    node.vm.hostname = "wvc-compute"
    node.vm.synced_folder ".", "/vagrant", type: "nfs",
      nfs_udp: false, 
      nfs_version: 4, 
      nfs_rsize: 8192, 
      nfs_wsize: 8192

    node.vm.network "private_network", 
      ip: "172.64.0.255",
      netmask: "255.255.255.0",
      auto_config: false,
      libvirt__dhcp_enabled: false,
      libvirt__network_name: "wvc-mgmt"
    
    node.vm.network "private_network", 
      ip: "192.168.33.255", 
      netmaks: "255.255.255.0", 
      auto_config: false,
      libvirt__dhcp_enabled: false,
      libvirt__network_name: "wvc-pub"
        
    node.vm.network "private_network", 
      ip: "10.132.0.255", 
      netmaks: "255.255.0.0",
      auto_config: false,
      libvirt__dhcp_enabled: false,
      libvirt__network_name: "wvc-priv"
        
    node.vm.provider :libvirt do |libvirt|
      libvirt.cpus = 6
      libvirt.cpu_mode = "host-passthrough"
      libvirt.memory = 8192
      libvirt.nested = true
      libvirt.machine_virtual_size = 256
      libvirt.qemu_use_session = false
    end 

    node.vm.provision "shell", run: "once", inline: <<-SHELL
      dnf install -y python3.9 cloud-utils-growpart
      growpart /dev/vda 4
      xfs_growfs /dev/vda4
    SHELL
  
    node.vm.provision "ansible" do |ansible|
      ansible.playbook = "scripts/dev/ansible/playbook.yml"
      ansible.extra_vars = {
        ansible_python_interpreter: "/usr/bin/python3.9"
      }
    end

  end
end
