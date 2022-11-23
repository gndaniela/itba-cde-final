#!/bin/bash -xe
#!/bin/bash
set -x
 
cat > /var/tmp/fix-bootstap.sh <<'EOF'
#!/bin/bash
set -x
 
while true; do
    NODEPROVISIONSTATE=`sed -n '/localInstance [{]/,/[}]/{
    /nodeProvisionCheckinRecord [{]/,/[}]/ {
    /status: / { p }
    /[}]/a
    }
    /[}]/a
    }' /emr/instance-controller/lib/info/job-flow-state.txt | awk ' { print $2 }'`
 
    if [ "$NODEPROVISIONSTATE" == "SUCCESSFUL" ]; then
        echo "Running my post provision bootstrap"
        # Enter your code here
        sudo python3 -m pip install --upgrade pip
        sudo python3 -m pip install boto3
        sudo python3 -m pip install botocore
        sudo python3 -m pip install scikit-learn
        sudo python3 -m pip install pyarrow
        sudo python3 -m pip install s3fs
        sudo python3 -m pip install numpy
        sudo python3 -m pip install pandas
        echo '-------BOOTSTRAP COMPLETE-------' 
 
        exit
    else
        echo "Sleeping Till Node is Provisioned"
        sleep 10
    fi
done
 
EOF
 
chmod +x /var/tmp/fix-bootstap.sh
nohup /var/tmp/fix-bootstap.sh  2>&1 &

#sudo python3 -m pip install numpy==1.15.4
#sudo python3 -m pip install pandas
#sudo pip install boto3 pyarrow s3fs scikit-learn
