# rpass.py

Raritan password utility to verify and change passwords on a number of Raritan intelligent PDUs.

## Quick start

Change to the directory where you have copied the `rpass.py` program.

Create a file called `hosts.txt` in this directory and put the names of your PDUs, one per line, in this file.

On Windows enter the following command:

```
python rpass.py username
```

On UNIX/Linux enter the following command:

```
./rpass.py username
```

In both cases change `username` to the username you use to login to your PDUs.

Enter your password when prompted.  Retype the password for verification.

The `rpass.py` program now checks to see if it can login to each PDU in the `hosts.txt` file
with your username and password.

If that is successful you are asked if you want to change your password.  Enter `y` or `yes`.

Now type a new password.  Retype the password for verification.

Now the password will be changed on each PDU.

Check you can login to your PDUs with the new password. HINT: use `rpass.py` a second time with the new password :-]

## Pre-requisites

You will need:

+ Python 3
+ The latest JSON-RPC SDK
+ The PYTHONPATH environment variable set to include the directory where the JSON-RPC SDK is

## Assumptions

You login to your PDUs with a username that is NOT the `admin` user.

You have the same password set on your PDUs.

## Restrictions

The `rpass.py` will not, currently, allow you to change the password for the `admin` user.  This is
a safety measure to prevent you accidently locking yourself out of all your PDUs!

## Error handling

If `rpass.py` has a problem at any point it will stop with a (hopefully) helpful error message.
Note that your PDUs could end up in a state
where some still have the old password and others have the new password.

## The --hostfile command line argument

You can specify a different host file using the `--hostfile` command line argument.  For example
if you have a file called `firstfloor.txt` which contains the names of all the PDUs on the
first floor you can run `rpass.py` as follows:

Windows:

```
python rpass.py --hostfile firstfloor.txt username
```

UNIX/Linux:

```
./rpass.py --hostfile firstfloor.txt username
```

This can be handy if you have groups of PDUs with different passwords between groups.

## Format of the `hosts.txt` file

The format of the `hosts.txt` file (or any file specified with the `--hostfile` command line
argument is one hostname per line.  IP addresses can also be specified.  Blank lines are ignored.
Also lines beginning with the `#` character are treated as comments and ignored.  This can be useful for
commenting out lines.

## Duplicate entries in the `hosts.txt` file

The `rpass.py` program will look for duplicates in the `hosts.txt` file.  If any are found an error
message is generated and the program exits.

Because a PDU could be known by a different name or it could be referred to by its name and it's IP address
the program also runs a second check to look for duplicates.  As each PDU is logged into the serial number is noted.  If
`rpass.py` encounters the serial number a second time the program issues an error message and exits.

------------------------------------------------

End of README.md
