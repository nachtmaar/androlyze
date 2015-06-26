
# encoding: utf-8

__author__ = "Lars Baumgärtner, Nils Schmidt"
__email__ = "{lbaumgaerner,schmidt89} at informatik.uni-marburg.de"

from androlyze import is_dyn_code, is_native_code

from androlyze.model.script.AndroScript import AndroScript

CAT_SSL = "SSL"
CAT_CODE_LOADING = "code loading"
CODE_LOADING_DYN = "dynamic"
CODE_LOADING_NATIVE = "native"

class SSL(AndroScript):
    ''' SSL Checks '''

    VERSION = "0.1"
    CHECKS = [
              ("Landroid/webkit/SslErrorHandler", "SSL_ERROR_HANDLER"),
              ("Ljava/net/Socket", "PLAIN_SOCKET"),
              ("Ljava/net/SocketFactory", "PLAIN_SOCKET_FACTORY"),
              ("Ljavax/net/ssl/SSLSocket", "SSL_SOCKET_STD"),
              ("Lorg/apache/http/conn/ssl/SSLSocket", "SSL_SOCKET_APACHE"),
              ("Ljavax/net/ssl/SSLSocketFactory", "SSL_SOCKET_FACTORY_STD"),
              ("Lorg/apache/http/conn/ssl/SSLSocketFactory", "SSL_SOCKET_FACTORY_APACHE"),
              ("EasySSLSocketFactory", "SSL_SOCKET_FACTORY_EASY"),
              ("Lcom/adobe/air/SSLSecurityDialog", "AIR_SSL_DIALOG"),
              ("Lorg/apache/http/conn/ssl/AllowAllHostnameVerifier", "HOSTNAME_VERIFIER_ALLOW_ALL"),
              ("Lorg/apache/http/conn/ssl/BrowserCompatHostnameVerifier", "HOSTNAME_VERIFIER_BROWSER_COMPAT"),
              ("Lorg/apache/http/conn/ssl/StrictHostnameVerifier", "HOSTNAME_VERIFIER_STRICT"),
              ("Lorg/apache/http/conn/ssl/X509HostnameVerifier", "HOSTNAME_VERIFIER_X509"),
              ("Ljavax/net/ssl/HttpsURLConnection", "URL_CONNECTION_HTTPS"),
              ("Ljava/net/HttpURLConnection", "URL_CONNECTION_HTTP"),
              ("Landroid/net/http/SslCertificate", "CERTIFICATE_CODE_STD"),
              ("Lcom/adobe/air/Certificate", "CERTIFICATE_CODE_AIR"),
              ("Lcom/google/ads/AdRequest", "GOOGLE_AD_SENSE"),
              ("Lcom/adobe/air", "ADOBE_AIR_RUNTIME")
              ]

    def _analyze(self, apk, dalvik_vm_format, vm_analysis, gvm_analysis, *args, **kwargs):
        '''
        Overwrite this function in apk subclass to build your own script!
        Use the `ResultObject` for logging.

        Parameters
        ----------
        apk: EAndroApk
        dalvik_vm_format: DalvikVMFormat
            Parsed .dex file.
            Only available if `needs_dalvik_vm_format` returns True.
        vm_analysis: VMAnalysis
            Dex analyzer.
            Only available if `needs_vmanalysis` returns True.
        gvm_analysis : GVMAnalysis
        '''
        res = self.res

        # register key
        res.register_bool_keys([CODE_LOADING_DYN, CODE_LOADING_NATIVE], CAT_CODE_LOADING)
        res.register_bool_keys(map(lambda t: t[1].lower(), self.CHECKS), CAT_SSL)

        # do checks
        self.do_usage_checks(vm_analysis)

    def do_usage_checks(self, dx):
        res = self.res

        def log(key):
            ''' convenience function for logging '''
            res.log_true(key, CAT_SSL)

        # run ssl checks
        for check_val, check_name in self.CHECKS:
            if dx.tainted_packages.search_packages(check_val) != []:
                # log
                log(check_name.lower())

        if is_dyn_code(dx):
            res.log_true(CODE_LOADING_DYN, CAT_CODE_LOADING)

        if is_native_code(dx):
            res.log_true(CODE_LOADING_NATIVE, CAT_CODE_LOADING)

        return res

    ############################################################
    #---Script requirements
    ############################################################

    def needs_xref(self):
        ''' Create cross references '''
        return True

def get_DynCode(dx):
    return dx.tainted_packages.search_packages( "Ldalvik/system/DexClassLoader")

if __name__ == '__main__':
    for res in AndroScript.test(SSL, ["../../../../testenv/apks/a2dp.Vol.apk"]):
        print res
        print res.write_to_json()