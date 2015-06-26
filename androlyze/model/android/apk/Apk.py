
# encoding: utf-8

__author__ = "Nils Tobias Schmidt"
__email__ = "schmidt89 at informatik.uni-marburg.de"

from collections import OrderedDict
from xml.dom import minidom

from androguard.core.bytecodes.apk import AXMLPrinter
from androlyze.loader.exception import CouldNotOpenApk
from androlyze.log.Log import log
from androlyze.model.analysis.result.StaticResultKeys import *
from androlyze.model.android.Constants import ANDROID_FILE_EXTENSION, \
    MANIFEST_ACTIVITY, MANIFEST_SERVICE, MANIFEST_RECEIVER, MANIFEST_PROVIDER, \
    MANIFEST_NS
from androlyze.model.script.impl.manifest.components import get_components_cache, \
    component_key_2_intent_key
from androlyze.util.Util import utc2local


class Apk(Hashable):
    ''' Defines an object for the basic attributes of an Apk file.

    See Also
    --------
    http://developer.android.com/guide/topics/manifest/manifest-intro.html
    '''

    def __init__(self):
        Hashable.__init__(self)
        self._package_name = None
        self._version_name = None
        self._import_date = None
        self._tag = None
        self._size_app_code = 0
        self._build_date = None

    def __eq__(self, other):
        if isinstance(other, Apk):
            return self is other or self.hash == other.hash
        return False

    def get_import_date(self):
        return self._import_date

    def set_import_date(self, value):
        self._import_date = value

    def del_import_date(self):
        del self._import_date

    def get_package_name(self):
        return self._package_name

    def get_version_name(self):
        return self._version_name

    def set_package_name(self, value):
        self._package_name = value

    def set_version_name(self, value):
        self._version_name = value

    def del_package_name(self):
        del self._package_name

    def del_version_name(self):
        del self._version_name

    def get_tag(self):
        return self._tag

    def set_tag(self, value):
        self._tag = value

    def del_tag(self):
        del self._tag

    def get_hash(self):
        '''
        Get the sha256 message digest of the apk file
        and store it.

        Returns
        -------
        str
            sha256 message digest as hexstring
        None
            If path is None

        Raises
        ------
        CouldNotOpenApk
            If the APK could no be opened
        '''
        try:
            return Hashable.get_hash(self)
        except OSError as e:
            raise CouldNotOpenApk(self.path, e)

    def get_size_app_code(self):
        return self._size_app_code

    def set_size_app_code(self, value):
        self._size_app_code = value

    def del_size_app_code(self):
        del self._size_app_code

    def get_build_date(self):
        ''' Get the date of the classes.dex file (build date).
        
        Returns
        -------
        datetime.datetime
            The build date.
        '''
        return self._build_date
            
    def set_build_date(self, value):
        self._build_date = value

    def del_build_date(self):
        del self._build_date        

    package_name = property(get_package_name, set_package_name, del_package_name, "str - Package name of the apk. Unique apk identifier (at least in the store)")
    version_name = property(get_version_name, set_version_name, del_version_name, "str - version")
    import_date = property(get_import_date, set_import_date, del_import_date, " datetime.datetime : the import date (default is None)")
    tag = property(get_tag, set_tag, del_tag, "str : some tag")
    size_app_code = property(get_size_app_code, set_size_app_code, del_size_app_code, "int : size of the uncompressed .dex file")
    build_date = property(get_build_date, set_build_date, del_build_date, "datetime.datetime : the build date (last timestamp of classes.dex) in zipfile")

    def __str__(self):
        SEP = '\n\t'
        res = self.short_description()
        res += '%ssha256: %s' % (SEP, self.hash)
        if self.import_date is not None:
            res += '%simport date: %s' % (SEP, utc2local(self.import_date))
        if self.path is not None:
            res += '%spath: %s' % (SEP, self.path)
        if self.tag is not None:
            res += "%stag: %s" % (SEP, self.tag)
        if self.size_app_code is not None:
            res += "%scode size: %d" % (SEP, self.size_app_code)
        if self.build_date is not None:
            res += "%sbuild date: %s" % (SEP, utc2local(self.build_date))
        return res

    def __repr__(self):
        return '%s(%s, %s, %s, %s, %s, %s)' % (self.__class__.__name__, self.package_name, self.version_name, self.hash, self.import_date, self.tag, self.build_date)

    def __hash__(self):
        return self.hash

    def __ne__(self, other):
        return not self == other

    def short_description(self):
        return '%s %s' % (self.package_name, self.version_name)

    def detailed_description(self):
        ''' Get a detailed description of the `Apk`. Includes package name, version name, hash, import date and path '''
        return unicode(self)

    def meta_dict(self):
        ''' Returns a sorted dictionary holding meta information of the APK file '''
        return OrderedDict([
                            (RESOBJ_APK_META,
                            OrderedDict([
                                         (RESOBJ_APK_META_PACKAGE_NAME, self.package_name),
                                         (RESOBJ_APK_META_VERSION_NAME, self.version_name),
                                         (self.KEY_HASH, self.hash),
                                         (RESOBJ_APK_META_IMPORT_DATE, self.import_date),
                                         (RESOBJ_APK_META_BUILD_DATE, self.build_date),
                                         (RESOBJ_APK_META_PATH, self.path),
                                         (RESOBJ_APK_META_TAG, self.tag)
                                       ])
                            )
                           ])

    def get_apk_filename_from_manifest(self):
        ''' Build the filename based on the manifest information (packageName and versionName) '''
        return '%s_%s.%s' % (self.package_name, self.version_name, ANDROID_FILE_EXTENSION)

    def set_meta(self, apk):
        '''
        Set the meta information from `apk`.

        Parameters
        ----------
        apk : Apk
            The `apk` from which the meta information will be taken
        '''
        pn, vn, _id, t, path, size_app_code, build_date = apk.package_name, apk.version_name, apk.import_date, apk.tag, apk.path, apk.size_app_code, apk.build_date
        if pn is not None:
            self.package_name = pn
        if vn is not None:
            self.version_name = vn
        if id is not None:
            self.import_date = _id
        if t is not None:
            self.tag = t
        if path is not None:
            self.path = path
        if size_app_code is not None:
            self.size_app_code
        if build_date is not None:
            self.build_date = build_date

    def app_code_comparator(self, other):
        ''' Comparator for app code size '''
        if None in (self.size_app_code, other.size_app_code):
            return 0
        return self.size_app_code - other.size_app_code
    
    def get_manifest_components_with_intent_filter(self):
        '''
        Get the package names which define an intent-filter.
        
        Returns
        -------
        set<str>
            Set of package names.
        '''
        res = set()
        # intents
        components_cache = get_components_cache(self)
    
        for k, package_names in components_cache.items():
            for package_name in package_names:
                # get intent filter for activity, service or receiver
                intent_key = component_key_2_intent_key(k)
                package_intents = self.get_intent_filters(intent_key, package_name) 
                if package_intents:
                    res.add(package_name)
                    
        return res

    def get_manifest_intent_filters(self, package_name, dalvik_syntax = True):
        ''' Check if the component specified through the `package_name` is callable from outside.
        
        Parameters
        ----------
        apk : Apk
        package_name: str
        dalvik_syntax: bool, optional (default is True)
            Expects the package name in the dalvik bytecode form like e.g. ("Lde/nachtmaar/myapp/myclass;")
            
        Returns
        -------
        list<dict>
            Lists the public components with their intent filters
            
        Example
        -------
        >>> get_manifest_intent_filters('Lorg.example.sqldemo.SQLDemo;')
        [{'activity': {'action': [u'android.intent.action.MAIN'], 'category': [u'android.intent.category.LAUNCHER']}}]
        '''
        if dalvik_syntax:
            package_name = package_name[1:]
            package_name = package_name.replace("/", ".")
            package_name = package_name[:-1]
            
        res = []
        for component_name in (MANIFEST_ACTIVITY, MANIFEST_SERVICE, MANIFEST_RECEIVER, MANIFEST_PROVIDER): 
            intent_filters = self.get_intent_filters(component_name, package_name)
            if intent_filters:
                res.append({component_name : intent_filters})
            
        return res
    
    def get_manifest_public_components(self):
        '''
        Get the package names which are publicly available.
        Either through an intent or through an explicit export
        
        Returns
        -------
        set<str>
            Set of package names.        
        '''
        return self.get_manifest_components_with_intent_filter().union(self.get_manifest_exported_components())
    
    # TODO: 
    def get_manifest_exported_components(self):
        '''
        Get the package names which are exported.
        
        Therefore the manifest looks like:
        "
            <activity android:name=".SQLDemo"
              android:exported="true">
        "
        
        Returns
        -------
        set<str>
            Set of package names.
        '''
        pns = set()
        for i in self.zip.namelist():
            if i == "AndroidManifest.xml":
                ap = AXMLPrinter(self.zip.read(i))
                dom = minidom.parseString(ap.get_buff())
                for component_type in (MANIFEST_ACTIVITY, MANIFEST_PROVIDER, MANIFEST_RECEIVER, MANIFEST_SERVICE):
                    component_tags = dom.getElementsByTagName(component_type)
                    # check that tag is available
                    for component_tag in component_tags:
                        component_attributes = component_tag.attributes
                        component_name = component_attributes.getNamedItemNS(MANIFEST_NS, "name").nodeValue 
                        
                        exported = False
                        exported_tag = component_attributes.getNamedItemNS(MANIFEST_NS, "exported")
                        if exported_tag:
                            exported = exported_tag.nodeValue
                            if exported.lower() == "true":
                                pns.add(component_name)
        return pns
                
                