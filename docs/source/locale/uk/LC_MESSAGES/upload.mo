��    
      l               �   I   �   !        )  $   =     b  "   s     �  %   �  �   �  �  \  �   S  !   �  -     D   :       E   �     �  <   �  �   0   All of the document uploading API endpoints follow the same set of rules. Content-Type: multipart/form-data Documents Uploading Form element should have name `file` HTTPie example:: Only one document can be uploaded. The cURL example:: The request itself should look like:: This is standard approach of HTML form file uploading defined by `RFC 1867 <http://www.faqs.org/rfcs/rfc1867.html>`_.  The requirements are: Project-Id-Version: openprocurement.api 0.1
Report-Msgid-Bugs-To: 
POT-Creation-Date: 2014-11-10 10:50+0200
PO-Revision-Date: 2014-11-10 12:36+0300
Last-Translator: Zoriana Zaiats <sorenabell@quintagroup.com>
Language: uk
Language-Team: Ukrainian <info@quintagroup.com>
Plural-Forms: nplurals=3; plural=(n%10==1 && n%100!=11 ? 0 : n%10>=2 && n%10<=4 && (n%100<10 || n%100>=20) ? 1 : 2)
MIME-Version: 1.0
Content-Type: text/plain; charset=utf-8
Content-Transfer-Encoding: 8bit
Generated-By: Babel 2.4.0
 Всі точки входу API завантаження документів використовують той самий набір правил. Content-Type: multipart/form-data Завантаження документів Елемент форми повинен мати назву `file`. Приклад HTTPie:: Завантажити можна лише один документ. Приклад cURL:: Сам запит повинен виглядати так:: Це стандартний підхід до HTML форми завантаження файлів, що визначається `RFC 1867 <http://www.faqs.org/rfcs/rfc1867.html>`_. Вимоги: 