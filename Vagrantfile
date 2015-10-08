# -*- mode: ruby -*-
# vi: set ft=ruby :

$script = <<SCRIPT
echo "Use 163 mirrors."
echo "deb http://mirrors.163.com/ubuntu/ trusty main restricted universe multiverse" > /etc/apt/sources.list
echo "deb http://mirrors.163.com/ubuntu/ trusty-security main restricted universe multiverse" >> /etc/apt/sources.list
echo "deb http://mirrors.163.com/ubuntu/ trusty-updates main restricted universe multiverse" >> /etc/apt/sources.list
SCRIPT

Vagrant.configure("2") do |config|
  config.vm.box = "ubuntu/trusty64"
  config.vm.box_check_update = false

  config.vm.network "private_network", ip: "192.168.30.10"

  config.vm.provider "virtualbox" do |vb|
    vb.customize ["modifyvm", :id, "--memory", "2014"]
  end

  # config.vm.provision :shell, inline: $script

  config.vm.provision :ansible do |ansible|
    ansible.verbose = 'vv'
    ansible.ask_vault_pass = true
    ansible.playbook = 'playbooks/vagrant.yml'
    ansible.limit = 'all'
  end

end
