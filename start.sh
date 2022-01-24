check() {
	package_name=$1
	version=$2

	if [[ $package_name == "nextcord[speed]" ]]; then
		python3 -c "import nextcord"
	elif [[ $package_name == "discord-together" ]]; then
		python3 -c "import discord_together"
	elif [[ $package_name == "npytdl" ]]; then
		python3 -c "import NPytdl"
	elif [[ $package_name == "pynacl" ]]; then
		python3 -c "import nacl"
	else
		python3 -c "import $package_name"
	fi

	result=$?
	if [[ $result -eq 1 ]]; then
		if [[ $package_name == "pysondb" ]]; then
			pip3 install "$package_name==$version"
		else
			pip3 install "$package_name>=$version"
		fi
	fi
}

install() {
	check "discord-together" "1.2.3"
	check "nextcord[speed]" "2.0.0a6"
	check "pyppeteer" "1.0.2"
	check "fastapi" "0.70.0"
	check "uvicorn" "0.15.0"
	check "npytdl" "4.1.0b2"
	check "orjson" "3.6.5"
	check "pynacl" "1.4.0"
	check "pysondb" "1.5.7"
}

install
clear

python3 main.py