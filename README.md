# SUSVM
A version manager for SUSPlayer, based on Python.
There are many other options built in, not to mention the ability to manage multiple versions.

***Notice: It only supports Windows, and will not be added in the future.***

![susvm_demo](https://user-images.githubusercontent.com/56142286/123508001-ca7cef80-d6a7-11eb-8a74-f076011426bc.png)

## Table of contents

* [Installation](#installation)
  * [Manual](#manual)
  * [Git](#git)
* [Usage](#usage)
  * [Environment Variables](#environment-variables)
    * [Required](#required)
      * [SUSVM: %USERPROFILE%\\\.susvm](#susvm-userprofilesusvm)
      * [SUSVM\_APP: %USERPROFILE%\\Desktop\\SUSPlayer](#susvm_app-userprofiledesktopsusplayer)
      * [PATH: %SUSVM%\\dist](#path-susvmdist)
    * [Optional](#optional)
      * [SUSVM\_HELPER: &lt;Path you want to set&gt;](#susvm_helper-path-you-want-to-set)
  * [Command](#command)
  * [Synchronization](#synchronization)
* [Migration Guide](#migration-guide)
  * [Resolve unmanaged SUSPlayer](#resolve-unmanaged-susplayer)
  * [Introduction of SUSVM](#introduction-of-susvm)
* [Development](#development)
* [Disclaimer](#disclaimer)
* [Author](#author)

## Installation

### Manual
If you don't have Git, or if you don't want to use Git for some reason, you can do it this way

1. Select the latest version of the [release](https://github.com/flatten-js/susvm/releases) from the page and download the file.

2. Rename the extracted file to ```.susvm``` and move it directly under your user folder.

### Git

1. Name the folder ```.susvm``` and create a clone.

    ```
    C:\> git clone https://github.com/flatten-js/susvm .susvm
    ```

2. Move the cloned ```.susvm``` folder to directly under the user folder.

## Usage

### Environment Variables
Please check the following for setting instructions  
See Also: [How To Set Environment Variables In Windows 10](https://www.alphr.com/environment-variables-windows-10/)

If you have a shell running, restart it after the configuration is complete.

#### Required

##### SUSVM: %USERPROFILE%\\.susvm
Path to the project folder

##### SUSVM_APP: %USERPROFILE%\\Desktop\\SUSPlayer
Path of the application folder to manage

##### PATH: %SUSVM%\\dist
Path of the distribution folder in the project folder

#### Optional

##### SUSVM_HELPER: \<Path you want to set\>
Path to the executable file to make it virtual full screen.  
See Also: [Borderless-Gaming](https://github.com/Codeusa/Borderless-Gaming)

### Command
**Command Prompt and Powershell should be launched with administrative privileges.**

Here are the basic commands.
Please check the help for details.

Display help.
```
C:\> susvm -h

# Learn more.
C:\> susvm <command> -h
```

Initialize the application, etc.
```
C:\> susvm init
```

Check the currently installed version.
```
C:\> susvm versions
```

Check the installable version.
```
C:\> susvm install -l
```

Install with a specific version.
```
C:\> susvm install -v <version> -p <pass>
```

Specify the version to use.
```
C:\> susvm use <version>
```

Start the application.  
Pressing and holding the I and K keys at the same time is the same as pressing the Esc key.
```
C:\> susvm start
```

### Synchronization

You can synchronize settings, music, scores, etc.  
To do this, simply put the files you want to synchronize into the master folder in the SUSPlayer folder.

If you want to benefit from the new version of the configuration, simply create a configuration file that contains only the configuration properties (key=value) that you want to synchronize.

```
# master/Config.ini

//Readmeに記載されているPassを入力してください。これにより利用規約に同意したものとみなされます。
Pass=<pass>

//プレイヤーネームを設定
PlayerName=Flat

//ウィンドウモードを指定できます。0...フルスクリーン 1...ウィンドウモード
WindowMode=1

//ウィンドウモードでの解像度を指定できます。横幅はXの値に合わせて自動調整されます。
WindowSizeX=2560

//オート再生するかどうかを指定できます。0...オート無効 1...オート有効
Auto=0

//スクロールスピードを指定できます。
//作者は普段9.0なのでそれにあわせて作りましたが多少のずれがあるかもしれません。
ScrollSpeed=9.5
```

If you want the changes in the master folder to be reflected, run the use command again.
```
C:\> susvm use <version>
```

## Migration Guide
The following is the procedure to migrate to version control using SUSVM when SUSPlayer is already installed.

### Resolve unmanaged SUSPlayer

1. Create a new folder with the folder name master. (Hereinafter referred to as the master folder)

2. Move the data you do not want to delete from the existing SUSPlayer to the master folder. (e.g. Config.ini, SUS, Score.ssc, etc.)

2. Delete SUSPlayer. (If you're afraid to delete it, just change its name to something other than SUSPlayer)

### Introduction of SUSVM

1. Follow [Installation](#installation) to install SUSVM.

2. Follow [Environment Variables](#environment-variables) to Set environment variables.

3. Launch Command Prompt or Powershell with administrative privileges.

4. Check if the settings are correct, etc.

    ```
    C:\> susvm -h
    usage: susvm [-h] {update,build,init,install,versions,use,start} ...
    ...
    ```

5. Initialize SUSVM.

    ```
    C:\> susvm init
    ```

6. Replace the master folder of the folder (SUSPlayer) created by initialization with the master folder created in [Resolve unmanaged SUSPlayer](#resolve-unmanaged-susplayer).

7. Check the versions available for installation.

    ```
    C:\> susvm install -l
    Available versions
    ...
    ```

8. Confirm the password from [SUSPlayer official Twitter](https://twitter.com/SUSPinfo) page and install the version.

    ```
    C:\> susvm install -v <version> -p <pass>
    Installation has been completed successfully.
    ```

9. Make sure it's installed.

    ```
    C:\> susvm versions
      <installed version>
    ```

10. Select the version you want to use.

    ```
    C:\> susvm use <installed version>
    Now using SUSPlayer <installed version>
    ```

11. Make sure you have selected the version you want to use.

    ```
    C:\> susvm versions
    * <use version> (Currently using executable)
    ```

12. Start SUSPlayer.

    ```
    C:\> susvm start
    <use version> is running now
    ```

For other options, please see [Usage](#usage).

## Development
If you are a Python engineer or other person who wants to edit the source, you can use -d during the init command to install the necessary Python packages.

```
C:\> susvm init -d
```

When you are done editing, you can build and overwrite the executable.

```
C:\> susvm build
```

## Disclaimer
Please note that we are not responsible for any damages caused in connection with the use of this SUSVM or other actions, regardless of the reason.

## Author
If you have any questions, please contact the following Twitter DM  
[Flat](https://twitter.com/this_world_girl)
