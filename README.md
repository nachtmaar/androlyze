AndroLyze
=========

About
-----

AndroLyze is a distributed framework for android app analysis with
unified logging and reporting functionality to perform security checks
on large numbers of applications in an efficient manner.

It provides optimized scheduling algorithms for distributing static code
analysis tasks across several machines. Moreover, it can handle several
versions of a single mobile application to generate a security track
record over many versions.

The code and documentation is related to the following paper (link will
follow):

![image](https://raw.githubusercontent.com/nachtmaar/androlyzedoc/master/gfx/androlyze_paper.png)

Features
--------

-   Static android code analysis based on
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

AndroLyze is licensed under the
[MIT](https://tldrlegal.com/license/mit-license) license.

Documentation
-------------

The documentation is hosted at
[readthedocs.org](https://androlyze.readthedocs.org) and opensource
available at [github](https://github.com/nachtmaar/androlyzedoc). Feel
free to contribute! Edit the docs on github, commit it and it will be
automatically built by readthedocs!
