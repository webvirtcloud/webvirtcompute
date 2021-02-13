# -*- mode: ruby -*-
# vi: set ft=ruby :

KVM_CPUS = 6
KVM_MEMORY = 4096
KVM_BOX = 'bento/centos-8.2'
HOME_DIR = ENV['HOME']

Vagrant.configure('2') do |config|
    config.ssh.insert_key = false
    config.vm.box = KVM_BOX
    config.vm.hostname = "host01"
    config.vm.provision "shell", path: "scripts/provision.sh"
    config.vm.network "private_network", ip: "172.32.16.10", auto_config: true

    # Virtualbox
    config.vm.provider :virtualbox do |vb|
        vb.name = "host01"
        vb.linked_clone = false
        vb.cpus = KVM_CPUS
        vb.memory = KVM_MEMORY
        vb.default_nic_type = "virtio"
        vb.customize ["modifyvm", :id, "--nested-hw-virt", "on"]

        disk = File.join("#{HOME_DIR}/VirtualBox VMs", vb.name, "disk1.vdi")
        unless File.exist?(disk)
            vb.customize ["createhd", "--filename", disk, "--size", 128 * 1024]
            vb.customize ["storageattach", :id,
                            "--storagectl", "SATA Controller",
                            "--port", 1,
                            "--device", 0,
                            "--type", "hdd",
                            "--medium", disk]
        end
    end

    # Parallels
    config.vm.provider :parallels do |prl|
        prl.name = "host01"
        prl.linked_clone = false
        prl.update_guest_tools = false
        prl.cpus = KVM_CPUS
        prl.memory = KVM_MEMORY
        prl.customize ["set", :id, "--nested-virt", "on"]

        disk = File.join("#{HOME_DIR}/Parallels", "#{prl.name}.pvm", "harddisk2.hdd/harddisk2.hdd")
        unless File.exist?(disk)
            prl.customize ["set", :id,
                            "--device-add", "hdd",
                            "--size", "131072",
                            "--iface", "sata"]
        end
    end

    # Libvirt
    config.vm.provider :libvirt do |lv, override|
        lv.cpus = KVM_CPUS
        lv.memory = KVM_MEMORY
        lv.nested = true
        lv.driver = "kvm"
        lv.disk_bus = "sata"
        lv.nic_model_type = "virtio"
        lv.storage :file, :size => "128G", :bus => "sata"
        override.vm.synced_folder ".", "/vagrant", type: "rsync", rsync__exclude: [".git/", ".vagrant/"]
    end
end
