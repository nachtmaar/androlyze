AndroLyze
=========

About
-----

AndroLyze is a distributed framework for android app analysis with
unified logging and reporting functionality to perform security checks
on large numbers of applications in an efficient manner. AndroLyze
provides optimized scheduling algorithms for distributing static code
analysis tasks across several machines. Moreover, AndroLyze can handle
several versions of a single mobile application to generate a security
track record over many versions.

Features
--------

-   Static code analysis based on
    [Androguard](https://github.com/androguard/androguard)
-   Unified logging and reporting framework backed by
    [mongoDB](https://www.mongodb.com)
-   Efficient Android app analysis on a single machine | local cluster |
    cloud
-   APK distribution via mongoDB, Amazon S3 or serialization of the
    local .apk files
-   Code-Size Scheduling: Schedule long running tasks first based on the
    size of the classes.dex file
-   Download APKs from [Google play](https://play.google.com/store) with
    the help of [Google Play
    Crawler](https://github.com/Akdeniz/google-play-crawler)
-   Update your APK collection by downloading the newest APK version to
    create a security track record over several versions

Try it out!
-----------

Still interested? Try it out! We provide an easy way to install
*AndroLyze* using [Docker](https://www.docker.com) containers.

License
-------

Licensed under the MIT license.
Check the documenation at [http://androlyze.readthedocs.org/en/latest/index.html](http://androlyze.readthedocs.org/en/latest/index.html)!
