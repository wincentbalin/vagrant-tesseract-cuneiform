# -*- mode: ruby -*-
# vi: set ft=ruby :

Vagrant.configure("2") do |config|
    config.vm.box = "ubuntu/xenial64"

    config.vm.provider "virtualbox" do |vb|
        vb.gui = false     # we log into here using ssh
        vb.cpus = "4"      # my computer has that many
        vb.memory = "16384" # for mftraining
        vb.customize ["modifyvm", :id, "--ioapic", "on"]
    end

    # Install mingw32 compiler and a couple of utilities
    config.vm.provision "shell", inline: <<-SHELL
    # Update packages
    apt-get update
    #apt-get upgrade -y
    # Install Tesseract together with training scripts
    apt-get install -y tesseract-ocr
    #wget https://raw.githubusercontent.com/tesseract-ocr/tesseract/3.04/training/{tesstrain,tesstrain_utils,language-specific}.sh
    wget https://raw.githubusercontent.com/tesseract-ocr/tesseract/master/training/{tesstrain,tesstrain_utils,language-specific}.sh
    chmod 0755 {tesstrain,tesstrain_utils,language-specific}.sh
    chown vagrant.vagrant {tesstrain,tesstrain_utils,language-specific}.sh
    # Install Cuneiform fonts
    apt-get install -y unzip
    FONTS_DIR=/usr/share/fonts
    wget http://oracc.museum.upenn.edu/downloads/{CuneiformOB,CuneiformNA,CuneiformComposite-1001}.zip
    unzip CuneiformOB.zip
    unzip CuneiformNA.zip
    unzip CuneiformComposite-1001.zip
    mv CuneiformOB.ttf CuneiformNA.ttf CuneiformComposite.ttf $FONTS_DIR
    rm CuneiformOB.zip CuneiformNA.zip CuneiformComposite-1001.zip
    # Copy Segoe UI Historic if present
    if [ -f /vagrant/seguihis.ttf ]
    then
        cp /vagrant/seguihis.ttf $FONTS_DIR
    fi
    fc-cache -fv
    text2image --fonts_dir $FONTS_DIR --list_available_fonts
    # Install additional training tools
    apt-get install -y git build-essential pkg-config libpango1.0-dev
    git clone https://ancientgreekocr.org/grctraining.git
    cd grctraining
    make tools/addmetrics tools/xheight
    strip tools/addmetrics tools/xheight
    cp tools/addmetrics tools/xheight /usr/local/bin
    cd ..
    # Setup user environment
    apt-get install -y vim mc tmux make
    ln -sf /vagrant /home/vagrant/host
SHELL
end
