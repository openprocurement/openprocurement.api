��    Z      �              �  ,   �  l   �     W  ?   k  �   �  A   1  !   s     �  (   �     �  :   �     .     6  ,   N  m   {  ,   �     	  4   (	  >   ]	     �	     �	     �	  	   �	  8   �	  G   
     f
  =   |
  B   �
  X   �
  X   V  N   �  /   �  #   .  S   R  *   �  >   �  +     3   <  )   p  -   �  ,   �  L   �  r   B     �  '   �  P   �  �   ?     �  "     !   *  '   L  o   t  F   �  .   +     Z  3   j  t   �          /     G      g  u   �     �  �    �   	  }   �  &   	  {   0  W   �  �     z   �       "        /      H     i  %   �  :   �  �   �  �   �     ?  P   �  B     �   S  J   �  D     �   d  M   
  W   X  u  �  L   &  �   s  /   `   j   �   �   �   �   �!  @   <"  %   }"  :   �"  @   �"  ]   #     }#  0   �#  u   �#  �   3$  J   "%  '   m%  Q   �%  l   �%  3   T&     �&  %   �&     �&  P   �&  p   2'  2   �'  [   �'  k   2(  �   �(  �   Y)  �   �)  J   �*  9   �*  u   +  L   �+  �   �+  K   ~,  �   �,  R   K-  L   �-  H   �-  �   4.  �   �.  )   Q/  @   {/  w   �/  6  40  9   k1  ;   �1  ;   �1  p   2  �   �2  x   \3  �   �3  )   h4  v   �4  �   	5  =   �5  4   �5  A   06  9   r6    �6  '   �7  '  �7  �   ;  �   �;  P   �<  G  �<  �   7>  �   �>  �   �?     @  C   �@  0   �@  T   A  1   ZA  s   �A  g    B    hB  %  �C  �   �D  �   lE  a   F  �   dF  k   ]G  o   �G  8  9H  �   rI  �   �I   Activating the request and cancelling tender After auction is scheduled anybody can visit it to watch. The auction can be reached at `Tender.auctionUrl`: And activate a bid: And again we can confirm that there are two documents uploaded. And again we have `201 Created` response code, `Location` header and body with extra `id`, `tenderID`, and `dateModified` properties. And bidders can find out their participation URLs via their bids: And indeed we have 2 tenders now. And individual answer: And one can retrieve the questions list: And upload proposal document: And we can see that it is overriding the original version: Auction Batch-mode registration Bidder can register a bid in `draft` status: By default contract value is set based on the award, but there is a possibility to set custom contract value. Cancel the tender with the reasons prepared. Cancelling tender Change the document description and other properties Checking the listing again reflects the new modification date: Confirming qualification Contract registration Creating tender Enquiries Error states that no `data` has been found in JSON body. Error states that the only accepted Content-Type is `application/json`. Exploring basic rules Fill it with the protocol describing the cancellation reasons Filling cancellation with protocol and supplementary documentation If this date is not set, it will be auto-generated on the date of contract registration. If you want to **lower contract value**, you can insert new one into the `amount` field. In case we made an error, we can reupload the document over the older version: It is possible to check the uploaded documents: Just invoking it reveals empty set. Let's access the URL of the created object (the `Location` header of the response): Let's check what tender registry contains: Let's create tender with the minimal (only required) data set: Let's satisfy the Content-type requirement: Let's see the list of all added contract documents: Let's see the list of contract documents: Let's see what listing of tenders reveals us: Let's try exploring the `/tenders` endpoint: Let's update tender by supplementing it with all other essential properties: Let’s add new `documentType` field with `technicalSpecifications` parameter to the previously uploaded document: Modifying tender Now let's attempt creating some tender: Now let’s try to modify any field in our document. For example, `description`: Only the request that has been activated (3rd step above) has power to cancel tender.  I.e.  you have to not only prepare cancellation request but to activate it as well. Prepare cancellation request Preparing the cancellation request Procuring entity can answer them: Procuring entity can set bid guarantee: Procuring entity can upload PDF files into the created tender. Uploading should follow the :ref:`upload` rules. Qualification comission registers its decision via the following call: Register bid with documents using one request: Registering bid See :ref:`cancellation` data structure for details. See the `Bid.participationUrl` in the response. Similar, but different, URL can be retrieved for other participants: Set contract signature date Setting  contract value Setting contract signature date Setting contract validity period Setting contract validity period is optional, but if it is needed, you can set appropriate `startDate` and `endDate`. Step-by-step registration Success! Now we can see that new object was created. Response code is `201` and `Location` response header reports the location of the created object.  The body of response reveals the information about the created tender: its internal `id` (that matches the `Location` segment), its official `tenderID` and `dateModified` datestamp stating the moment in time when tender was last modified. Pay attention to the `procurementMethodType`. Note that tender is created with `active.enquiries` status. Success! Response code is `200 OK` and it confirms that `documentType` field with `technicalSpecifications` parameter was added . Tender creator can cancel tender anytime (except when tender has terminal status e.g. `usuccesfull`, `canceled`, `complete`). The following steps should be applied: The previous tender contained only required fields. Let's try creating tender with more data (tender has status `created`): The single array element describes the uploaded document. We can upload more documents: There is a possibility to set custom contract signature date. If the date is not set it will be generated on contract registration. There is a possibility to set custom contract signature date. You can insert appropriate date into the `dateSigned` field. Tutorial Upload new version of the document Upload the file contents Uploading contract documentation Uploading documentation We can add another contract document: We can see the same response we got after creating tender. We do see the internal `id` of a tender (that can be used to construct full URL by prepending `http://api-sandbox.openprocurement.org/api/0/tenders/`) and its `dateModified` datestamp. We see the added properies have merged with existing tender data. Additionally, the `dateModified` property was updated to reflect the last modification datestamp. When ``Tender.tenderingPeriod.startDate`` comes, Tender switches to `active.tendering` status that allows registration of bids. When tender is in `active.enquiry` status, interested parties can ask questions: You can upload contract documents. Let's upload contract document: You should pass `reason`, `status` defaults to `pending`. `id` is autogenerated and passed in the `Location` header of response. `200 OK` response was returned. The description was modified successfully. `200 OK` response was returned. The value was modified successfully. `201 Created` response code and `Location` header confirm document creation. We can additionally query the `documents` collection API endpoint to confirm the action: `201 Created` response code and `Location` header confirm document was added. `201 Created` response code and `Location` header confirm second document was uploaded. Project-Id-Version: openprocurement.api 0.1
Report-Msgid-Bugs-To: 
POT-Creation-Date: 2016-10-19 16:04+0300
PO-Revision-Date: 2016-10-19 17:40+0200
Last-Translator: Zoriana Zaiats <sorenabell@quintagroup.com>
Language-Team: Ukrainian <info@quintagroup.com>
MIME-Version: 1.0
Content-Type: text/plain; charset=utf-8
Content-Transfer-Encoding: 8bit
Generated-By: Babel 2.3.4
 Активація запиту та скасування закупівлі Після того, як аукціон заплановано, будь-хто може його відвідати для перегляду. Аукціон можна подивитись за допомогою `Tender.auctionUrl`: Та активувати пропозицію: І знову можна перевірити, що є два завантажених документа. І знову код відповіді `201 Created`,  заголовок `Location` і тіло з додатковим `id`, `tenderID`, та властивість `dateModified`. Учасники можуть дізнатись свої URL-адреси для участі через свої пропозиції: Дійсно, в нас зараз є дві закупівлі. та окрему відповідь: Можна отримати список запитань: І завантажити документ пропозиції: І ми бачимо, що вона перекриває оригінальну версію: Аукціон Пакетний режим реєстрації Учасник може зареєструвати пропозицію у статусі `draft` (чернетка): За замовчуванням вартість угоди встановлюється на основі рішення про визначення переможця, але є можливість змінити це значення. Скасуйте закупівлю через подані причини Скасування закупівлі Зміна опису документа та інших властивостей Ще одна перевірка списку відображає нову дату модифікації: Підтвердження кваліфікації Реєстрація угоди Створення закупівлі Уточнення Помилка вказує, що `data` не знайдено у тілі JSON. Помилка вказує, що єдиний прийнятний тип вмісту це `application/json`. Розглянемо основні правила Наповніть його протоколом про причини скасування Наповнення протоколом та іншою супровідною документацією Якщо ви не встановите дату підписання, то вона буде згенерована автоматично під час реєстрації угоди. Якщо ви хочете **знизити вартість угоди**, ви можете встановити нове значення для поля `amount`. Якщо сталась помилка, ми можемо ще раз завантажити документ поверх старої версії: Можна перевірити завантажені документи: При виклику видає пустий набір. Використаємо URL створеного об’єкта (заголовок відповіді `Location`): Перевіримо, що містить реєстр закупівель: Створимо закупівлю з мінімально допустимим (обовязковим для заповнення) набором даних: Задовольнимо вимогу типу вмісту (Content-type): Тепер переглянемо знову усі документи пов’язані із укладанням угоди: Переглянемо список завантажених документів: Подивимось, що показує список закупівель: Подивимось як працює точка входу `/tenders`: Оновимо закупівлю шляхом надання їй усіх інших важливих властивостей: Додамо нове поле `documentType` з параметром `technicalSpecifications` до вже завантаженого документа. Модифікація закупівлі Спробуймо створити нову закупівлю: Можна змінити будь-яке поле в документі. Наприклад, `description` (опис): Запит на скасування, який не пройшов активації (3-й крок), не матиме сили, тобто, для скасування закупівлі буде обов’язковим не тільки створити заявку, але і активувати її. Приготуйте запит на скасування Формування запиту на скасування Замовник може на них відповісти: Замовник може встановити забезпечення тендерної пропозиції: Замовник може завантажити PDF файл у створену закупівлю. Завантаження повинно відбуватись згідно правил :ref:`upload`. Кваліфікаційна комісія реєструє своє рішення через такий виклик: У пакетному режимі (batch-mode) є можливість зареєструвати пропозицію одним запитом: Реєстрація пропозиції Див. структуру запиту :ref:`cancellation` для більш детальної інформації. Дивіться на `Bid.participationUrl` у відповіді. Схожу, але іншу, URL-адресу можна отримати для інших учасників. Встановити дату підписання угоди Встановлення вартості угоди Встановлення дати підписання угоди Встановлення терміну дії угоди Встановлення терміну дії угоди необов’язкове, але, якщо є необхідність, ви можете встановити відповідну дату початку `startDate` та кінця `endDate` терміну дії. Покрокова реєстрація Успіх! Тепер ми бачимо, що новий об’єкт було створено. Код відповіді `201` та заголовок відповіді `Location` вказує місцерозташування створеного об’єкта. Тіло відповіді показує інформацію про створену закупівлю, її внутрішнє `id` (яке співпадає з сегментом `Location`), її офіційне `tenderID` та `dateModified` дату, що показує час, коли закупівля востаннє модифікувалась. Зверніть увагу на `procurementMethodType`, а також на те, що закупівля створюється зі статусом `active.enquiries`. Успіх! Код відповіді `200 OK` підтверджує, що поле `documentType` з параметром `technicalSpecifications` було додано. Замовник може скасувати закупівлю у будь-який момент (крім закупівель у кінцевому стані, наприклад, `usuccesfull`, `canceled`, `complete`). Для цього потрібно виконати наступні кроки: Попередня закупівля була створена лише з обов’язковими полями. Тепер додамо закупівлю з максимально допустимим набором даних при створенні (тендер повинен бути у статусі `created`). Один елемент масиву описує завантажений документ. Ми можемо завантажити більше документів: Є можливість встановити дату підписання договору. Якщо дата не встановлена, то вона буде згенерована під час реєстрації договору. Є можливість встановити дату підписання угоди. Для цього вставте відповідну дату в поле `dateSigned`. Туторіал Завантаження нової версії документа Завантаження вмісту файлу Завантаження документів щодо укладання угоди Завантаження документації Тепер спробуємо додати ще один документ щодо укладанням угоди: Ми бачимо ту ж відповідь, що і після створення закупівлі. Ми бачимо внутрішнє `id` закупівлі (що може бути використано для побудови повної URL-адреси, якщо додати `http://api-sandbox.openprocurement.org/api/0/"-"tenders/`) та її `dateModified` дату. Ми бачимо, що додаткові властивості об’єднані з існуючими даними закупівлі. Додатково оновлена властивість `dateModified`, щоб відображати останню дату модифікації. Коли приходить ``Tender.tenderingPeriod.startDate``, Закупівля отримує статус `active.tendering`, що дозволяє реєстрацію пропозицій. Коли закупівля має статус `active.enquiry`, зацікавлені сторони можуть задавати питання: Спробуємо завантажити документ пов’язаний з угодою: Ви повинні передати змінні `reason`, `status` у стані `pending`. `id` генерується автоматично і повертається у додатковому заголовку відповіді `Location`: Повернено код `200 OK`, тобто опис було успішно відредаговано. Було повернуто код відповіді `200 OK`. Значення змінено успішно. Код відповіді `201 Created` та заголовок `Location` підтверджують, що документ було створено. Додатково можна зробити запит точки входу API колекції `документів`, щоб підтвердити дію: Код відповіді `201 Created` та заголовок `Location` підтверджують, що документ додано. Код відповіді `201 Created`та заголовок `Location` підтверджують, що ще один документ було додано. 