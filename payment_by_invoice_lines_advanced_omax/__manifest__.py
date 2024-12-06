# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
{
	'name': 'Partial Payment by Invoice/Bill Lines Advanced',
	'version': '16.0',
	'author': 'OMAX Informatics',
	'description': """ Partial Payment by Invoice/Bill lines""",
	'category': 'Accounting',
	'website': 'https://www.omaxinformatics.com',
	'depends': [
		'account','payment_by_invoice_lines_omax',
	],
	'data': [
	    'security/ir.model.access.csv',
	    'wizard/account_payment_register.xml',
	    'views/account_move.xml',
	    'report/report.xml',
	],
	'demo': [],
	'test': [],
    'qweb': [],
	"images": ["static/description/banner.png",],
    'license': 'AGPL-3',
    'currency':'USD',
    'price': 40.0,
    'installable' : True,
    "auto_install" : False,
    "application" : True,
    'live_test_url': 'https://youtu.be/sexvKcM98_4',
    "pre_init_hook": "pre_init_check",
	'summary': """ 
	This app allow user to pay by invoice and bill line as well as pay partially for selected lines,
	Partial Payment by Invoice lines,Partial Payment by Bill lines,
	partial payment for invoie lines,partial payment for Bill lines,
	Payment by invoice lines, Payment by bill lines,partial payment,
	payment, partial, register payment by lines,
	partial payment by lines,
	partial payment by inoice lines,partial payment by bill lines,
	lines paid report, lines unpaid report,
	lines paid unpaid report,
	lines partial paid report,
	partial payment register,Customer payment,
	Customer invoice,Vendor bill,customer invoice payment,vendor bill payment,
	register payment,payment,partial,customer,invoice, Bill
	paid report,unpaid report,partial payment report,
	report for partial payment,customer payment report,
	customer payment,customer partial payment,
	partial customer payment,paid,unpaid,register payment,
	invoice line,bill line,invoice line payment,bill line payment, line wise payment,
	partial payment,partial payment report,customer invoice report,vendor bill report,
	customer invoice, Vendor bill
	partial payment in invoice partial payment in Bill partial payment for inoice lines partial payment for bill lines Multiple Vendor Payment Multiple Bill Payment Multiple Customer Payment Multiple Invoice Payment Credit Notes multiple payments reconcile payments in invoice reconcile payments in bill Partial invoice payments Partial bill payments Partial reconcile invoice payments reconcile bill payments reconcile journal entry reconcile journal entries reconcile entry adjust journal entry adjust journal entries adjust entry Pay invoice Payment for invoice reconcile with invoice reconcile with payment Pay bill Payment for bill reconcile with bill reconcile payment in invoice reconcile payment in bill Auto Reconcile Credit Notes with Invoice Auto Reconcile Credit Notes with bill Mass Register Payment
    Partial Payment on Invoice Lines Partial payment by line item Invoice line partial payment Paying part of an invoice item Partial payment per invoice line Line-Level Payment Processing Payment on specific invoice lines Partial payment for individual items Line-wise payment processing Paying specific items on an invoice Invoice Item Partial Payment Partially paying invoice items Payment for specific invoice products Individual item payment on invoices Partial settlement by item Selective Invoice Payments Selective payment on invoices Choosing items for partial payment Partially paying selected items Specific item payment on invoices Partial Settlement by Line Settling part of an invoice line Partial settlement for each item Payment on a line-by-line basis Settling specific items on an invoice Line-Specific Payment Transactions Payment transactions by line Partial payment transactions Processing payments by item Individual item payment records Invoice Line Payment Allocation Allocating payment to specific lines Partial payment allocation Payment distribution by line Allocating payment to individual items Itemized Invoice Payments Itemized payment on invoices Payment breakdown by line Paying specific items  separately Partial payment details by item Partial Payment Tracking partial payments Payment history by line Monitoring partial payment transactions Payment tracking for individual items Line-Level Invoice Settling invoices at the line level Partial settlement by line item Payment at the invoice item level Individual item settlement on invoices

Cette application permet à l'utilisateur de payer par facture et ligne de facture ainsi que de payer partiellement les lignes sélectionnées,
Paiement partiel par lignes de facture, Paiement partiel par lignes de facture,
paiement partiel pour les lignes de réception, paiement partiel pour les lignes de facture,
Paiement par lignes de facture, Paiement par lignes de facture, paiement partiel,
paiement, partiel, enregistrer le paiement par lignes,
paiement partiel par lignes,
paiement partiel par lignes de facture, paiement partiel par lignes de facture,
rapport des lignes payées, rapport des lignes non payées,
rapport lignes payées impayées,
lignes rapport partiellement payé,
registre de paiement partiel, paiement client,
Facture client, facture fournisseur, paiement de facture client, paiement de facture fournisseur,
enregistrer le paiement,paiement,partiel,client,facture, facture
rapport payé, rapport impayé, rapport de paiement partiel,
rapport de paiement partiel, rapport de paiement client,
paiement client, paiement partiel client,
paiement partiel du client, payé, impayé, paiement d'enregistrement,
ligne de facture, ligne de facture, paiement de ligne de facture, paiement de ligne de facture, paiement par ligne,
Paiement partiel, rapport de paiement partiel, rapport de facture client, rapport de facture fournisseur,
facture client, facture fournisseur

paiement partiel dans la facture paiement partiel dans la facture paiement partiel pour les lignes de facture paiement partiel pour les lignes de facture Paiement de fournisseurs multiples Paiement de factures multiples Paiement de client multiple Paiement de facture multiple Notes de crédit paiements multiples rapprochement paiements dans facture rapprochement paiements dans facture Paiements de facture partiels Paiements de facture partiels Rapprochement partiel paiements de factures rapprocher les paiements de factures rapprocher l'écriture de journal rapprocher les écritures de journal rapprocher l'entrée ajuster l'écriture de journal ajuster les écritures de journal ajuster l'entrée Payer la facture Paiement de la facture rapprocher avec la facture rapprocher avec le paiement Payer la facture Paiement de la facture rapprocher avec la facture rapprocher le paiement dans la facture rapprocher le paiement dans la facture Rapprochement automatique Notes de crédit avec facture Rapprochement automatique des notes de crédit avec facture Registre de masse Paiement
     Paiement partiel sur les lignes de facture Paiement partiel par article de ligne Paiement partiel de ligne de facture Paiement d'une partie d'un article de facture Paiement partiel par ligne de facture Traitement des paiements au niveau de la ligne Paiement sur des lignes de facture spécifiques Paiement partiel pour des articles individuels Traitement des paiements par ligne Paiement d'articles spécifiques sur un facture Article de facture Paiement partiel Paiement partiel d'articles de facture Paiement de produits de facture spécifiques Paiement d'article individuel sur factures Règlement partiel par article Paiements de facture sélectifs Paiement sélectif sur factures Choix d'articles pour un paiement partiel Paiement partiel d'articles sélectionnés Paiement d'article spécifique sur factures Règlement partiel par ligne Partie de règlement d'une ligne de facture Règlement partiel pour chaque article Paiement ligne par ligne Règlement d'articles spécifiques sur une facture Opérations de paiement spécifiques à une ligne Opérations de paiement par ligne Opérations de paiement partiel Traitement des paiements par article Enregistrements de paiement d'article individuel Ligne de facture Allocation de paiement Affectation de paiement à des lignes spécifiques Répartition des paiements partiels Répartition des paiements par ligne Affectation du paiement aux postes individuels Paiements de factures détaillés Paiement détaillé sur les factures Répartition des paiements par ligne Payer des postes spécifiques séparément Détails des paiements partiels par poste Suivi des paiements partiels Paiements partiels Historique des paiements par ligne Suivi des opérations de paiement partiel Suivi des paiements pour les articles individuels Facture au niveau de la ligne Règlement des factures au niveau de la ligne Règlement partiel par article de la ligne Paiement au niveau des articles de facture Règlement des articles individuels sur les factures

Esta aplicación permite al usuario pagar mediante factura y línea de factura, así como pagar parcialmente por líneas seleccionadas.
Pago parcial por líneas de factura,Pago parcial por líneas de factura,
pago parcial de líneas de factura,pago parcial de líneas de factura,
Pago por líneas de factura, Pago por líneas de factura, pago parcial,
pago, parcial, registro pago por líneas,
pago parcial por líneas,
pago parcial por líneas de factura,pago parcial por líneas de factura,
informe de líneas pagadas, informe de líneas no pagadas,
informe de líneas pagadas no pagadas,
líneas de informe parcialmente pagado,
registro de pago parcial, pago del cliente,
Factura de cliente, factura de proveedor, pago de factura de cliente, pago de factura de proveedor,
registrar pago, pago, parcial, cliente, factura, factura
informe pagado, informe no pagado, informe de pago parcial,
informe de pago parcial, informe de pago del cliente,
pago del cliente, pago parcial del cliente,
pago parcial del cliente, pagado, no pagado, pago de registro,
línea de factura, línea de factura, pago de línea de factura, pago de línea de factura, pago por línea,
pago parcial, informe de pago parcial, informe de factura del cliente, informe de factura del proveedor,
factura de cliente, factura de proveedor

pago parcial en factura pago parcial en factura pago parcial de líneas de factura pago parcial de líneas de factura Pago de múltiples proveedores Pago de facturas múltiples Pago de clientes múltiples Pago de facturas múltiples Notas de crédito pagos múltiples conciliar pagos en factura conciliar pagos en factura Pagos de factura parcial Pagos de factura parciales Conciliación parcial pagos de facturas conciliar pagos de facturas conciliar asiento de diario conciliar asientos de diario conciliar asiento ajustar asiento de diario ajustar asientos de diario ajustar asiento Pagar factura Pago de factura conciliar con factura conciliar con pago Pagar factura Pago de factura conciliar con factura conciliar pago en factura conciliar pago en factura Conciliación automática Notas de crédito con factura Conciliación automática de notas de crédito con factura Registro masivo Pago
     Pago parcial en líneas de factura Pago parcial por artículo de línea Pago parcial de línea de factura Pago de parte de un artículo de factura Pago parcial por línea de factura Procesamiento de pago a nivel de línea Pago en líneas de factura específicas Pago parcial de artículos individuales Procesamiento de pago por línea Pago de artículos específicos en un Factura Artículo de factura Pago parcial Pago parcial de artículos de factura Pago de productos de factura específicos Pago de artículos individuales en facturas Liquidación parcial por artículo Pagos selectivos de facturas Pago selectivo de facturas Elección de artículos para pago parcial Pago parcial de artículos seleccionados Pago de artículos específicos en facturas Liquidación parcial por línea Liquidación parcial de una línea de factura Liquidación parcial para cada artículo Pago línea por línea Liquidación de artículos específicos en una factura Transacciones de pago de línea específica Transacciones de pago por línea Transacciones de pago parcial Procesamiento de pagos por artículo Registros de pago de artículos individuales Asignación de pago de línea de factura Asignación de pago a líneas específicas Asignación de pagos parciales Distribución de pagos por línea Asignación de pagos a artículos individuales Pagos de facturas detallados Pago detallado en facturas Desglose de pagos por línea Pago de artículos específicos por separado Detalles de pagos parciales por artículo Pago parcial Seguimiento de pagos parciales Historial de pagos por línea Monitoreo de transacciones de pagos parciales Seguimiento de pagos para artículos individuales Factura a nivel de línea Liquidación de facturas a nivel de línea Liquidación parcial por artículo en línea Pago a nivel de artículo de factura Liquidación de artículo individual en facturas
该应用程序允许用户通过发票和帐单行付款以及部分支付选定的行，
按发票行部分付款、按账单行部分付款、
发票行的部分付款、票据行的部分付款、
按发票行付款、按账单行付款、部分付款、
付款，部分付款，按行登记付款，
按行部分付款，
按发票行部分付款、按帐单行部分付款、
已付行数报告、未付行数报告、
行已付未付报告，
行部分付费报告，
部分付款登记，客户付款，
客户发票、供应商账单、客户发票付款、供应商账单付款、
登记付款、付款、部分、客户、发票、账单
已付款报告、未付款报告、部分付款报告、
部分付款报告、客户付款报告、
客户付款、客户部分付款、
部分客户付款、已付款、未付款、登记付款、
发票行，账单行，发票行付款，账单行付款，按行付款，
部分付款、部分付款报告、客户发票报告、供应商账单报告、
客户发票、供应商账单

发票中的部分付款 账单中的部分付款 账单行的部分付款 账单行的部分付款 多个供应商付款 多个账单付款 多个客户付款 多个发票付款 信用票据 多个付款 发票中的对账付款 账单中的付款对账 部分发票付款 部分账单付款 部分对账 发票付款 核对账单付款 核对日记账分录 核对日记账分录 核对分录 调整日记账分录 调整日记账分录 调整分录 支付发票 付款发票 与发票核对 与付款核对 支付账单 账单付款 与账单核对 发票中的付款 核对账单中的付款 自动核对 贷项票据与发票自动核对贷项票据与账单批量注册付款
     发票行的部分付款 按行项目的部分付款 发票行的部分付款 支付发票项目的一部分 按发票行的部分付款 行级付款处理 在特定发票行上的付款 单个项目的部分付款 按行付款处理 支付某个发票上的特定项目 发票 发票项目 部分付款 部分支付发票项目 针对特定发票产品的付款 发票上的单个项目付款 按项目进行部分结算 选择性发票付款 发票上的选择性付款 选择部分付款的项目 部分支付所选项目 发票上的特定项目付款 按行部分结算 结算部分 发票行的每个项目的部分结算 逐行付款 结算发票上的特定项目 特定行付款交易 按行付款交易 部分付款交易 按项目处理付款 单个项目付款记录 发票行付款分配 分配付款 到特定行 部分付款分配 按行付款分配 将付款分配到各个项目 明细发票付款 发票上的明细付款 按行付款明细 单独支付特定项目 按项目的部分付款详细信息 部分付款跟踪部分付款 按行的付款历史记录 监控部分付款交易 付款跟踪 对于单个项目 行级发票 在行级结算发票 按行项目部分结算 在发票项目级付款 在发票上的单个项目结算

Met deze app kan de gebruiker betalen per factuur- en factuurregel en gedeeltelijk betalen voor geselecteerde regels,
Gedeeltelijke betaling per factuurregels,Gedeeltelijke betaling per factuurregels,
gedeeltelijke betaling voor factuurregels, gedeeltelijke betaling voor factuurregels,
Betaling per factuurregels, Betaling per factuurregels, gedeeltelijke betaling,
betaling, gedeeltelijk, betaling per lijn registreren,
gedeeltelijke betaling per lijn,
gedeeltelijke betaling via factuurregels, gedeeltelijke betaling via factuurregels,
betaald lijnenrapport, lijnen onbetaald rapport,
lijnen betaald onbetaald rapport,
lijnen gedeeltelijk betaald rapport,
register voor gedeeltelijke betaling, klantbetaling,
Klantfactuur, leveranciersrekening, betaling van klantfactuur, betaling van leveranciersrekening,
registreren betaling,betaling,gedeeltelijk,klant,factuur, factuur
betaald rapport, onbetaald rapport, rapport gedeeltelijke betaling,
rapport voor gedeeltelijke betaling, klantbetalingsrapport,
klantbetaling, gedeeltelijke betaling van de klant,
gedeeltelijke klantbetaling,betaald,onbetaald,betaling registreren,
factuurregel, factuurregel, factuurregelbetaling, factuurregelbetaling, regelgewijze betaling,
gedeeltelijke betaling, rapport gedeeltelijke betaling, rapport klantfactuur, rapport leveranciersrekening,
klantfactuur, leveranciersrekening

gedeeltelijke betaling op factuur gedeeltelijke betaling op factuur gedeeltelijke betaling voor factuurregels gedeeltelijke betaling voor factuurregels Meerdere leveranciersbetaling Meerdere factuurbetaling Meerdere klantbetalingen Meerdere factuurbetalingen Creditnota's meerdere betalingen afstemmen betalingen op factuur afstemmen betalingen op factuur Gedeeltelijke factuurbetalingen Gedeeltelijke factuurbetalingen Gedeeltelijk afstemmen factuurbetalingen rekeningbetalingen afstemmen journaalboeking afstemmen journaalboekingen afstemmen boeking aanpassen journaalboeking aanpassen journaalposten aanpassen boeking aanpassen Factuur betalen Betaling voor factuur afstemmen met factuur afstemmen met betaling Factuur betalen Betaling voor factuur afstemmen met factuur afstemmen betaling op factuur afstemmen betaling op factuur Automatisch afstemmen Creditnota's met factuur Automatisch afstemmen van creditnota's met factuur Massaregistratiebetaling
     Gedeeltelijke betaling op factuurregels Gedeeltelijke betaling per regel Gedeeltelijke betaling factuurregel Betalen van een deel van een factuurartikel Gedeeltelijke betaling per factuurregel Betalingsverwerking op regelniveau Betaling op specifieke factuurregels Gedeeltelijke betaling voor afzonderlijke artikelen Regelgewijze betalingsverwerking Betalen van specifieke artikelen op een factuur Factuuritem Gedeeltelijke betaling Gedeeltelijk betalen van factuuritems Betaling voor specifieke factuurproducten Afzonderlijke itembetaling op facturen Gedeeltelijke afrekening per item Selectieve factuurbetalingen Selectieve betaling op facturen Artikelen kiezen voor gedeeltelijke betaling Gedeeltelijk betalen van geselecteerde items Specifieke itembetaling op facturen Gedeeltelijke afrekening per regel Afrekeningsgedeelte van een factuurregel Gedeeltelijke afrekening per artikel Betaling per regel Afrekenen van specifieke artikelen op een factuur Regelspecifieke betalingstransacties Betalingstransacties per regel Deelbetalingstransacties Betalingen per artikel verwerken Betalingsrecords voor individuele artikelen Factuurregel Betalingstoewijzing Toewijzing van betaling aan specifieke regels Gedeeltelijke betalingstoewijzing Betalingsverdeling per regel Toewijzing van betaling aan individuele artikelen Gespecificeerde factuurbetalingen Gespecificeerde betaling op facturen Betalingsverdeling per regel Specifieke artikelen afzonderlijk betalen Gedeeltelijke betalingsgegevens per artikel Gedeeltelijke betaling Traceren van gedeeltelijke betalingen Betalingsgeschiedenis per regel Monitoren van gedeeltelijke betalingstransacties Betalingen volgen voor individuele artikelen Factuur op regelniveau Facturen afrekenen op regelniveau Gedeeltelijke verrekening per regel Betaling op factuurpositieniveau Afzonderlijke artikelafrekening op facturen
Mit dieser App können Benutzer per Rechnung und Rechnungszeile bezahlen sowie teilweise für ausgewählte Zeilen bezahlen.
Teilzahlung nach Rechnungszeilen, Teilzahlung nach Rechnungszeilen,
Teilzahlung für Rechnungszeilen, Teilzahlung für Rechnungszeilen,
Zahlung nach Rechnungsposten, Zahlung nach Rechnungsposten, Teilzahlung,
Zahlung, teilweise, Zahlung nach Zeilen registrieren,
Teilzahlung nach Zeilen,
Teilzahlung nach Rechnungszeilen, Teilzahlung nach Rechnungszeilen,
Bericht über bezahlte Leitungen, Bericht über unbezahlte Leitungen,
Zeilen bezahlt unbezahlt Bericht,
Zeilen teilweise bezahlter Bericht,
Teilzahlungsregister, Kundenzahlung,
Kundenrechnung, Kreditorenrechnung, Zahlung der Kundenrechnung, Zahlung der Kreditorenrechnung,
Registrieren Sie Zahlung, Zahlung, Teilzahlung, Kunde, Rechnung, Rechnung
bezahlter Bericht, unbezahlter Bericht, Teilzahlungsbericht,
Bericht für Teilzahlung, Kundenzahlungsbericht,
Kundenzahlung, Kundenteilzahlung,
Teilzahlung des Kunden, bezahlt, unbezahlt, Zahlung registrieren,
Rechnungsposten, Rechnungsposten, Rechnungspostenzahlung, Rechnungspostenzahlung, zeilenweise Zahlung,
Teilzahlung, Teilzahlungsbericht, Kundenrechnungsbericht, Kreditorenrechnungsbericht,
Debitorenrechnung, Kreditorenrechnung

Teilzahlung in der Rechnung, Teilzahlung in der Rechnung, Teilzahlung für Rechnungszeilen, Teilzahlung für Rechnungszeilen, mehrere Lieferantenzahlungen, mehrere Rechnungszahlungen, mehrere Kundenzahlungen, mehrere Rechnungszahlungen, Gutschriften, mehrere Zahlungen, Zahlungen auf der Rechnung abgleichen, Zahlungen auf der Rechnung abgleichen, Teilrechnungszahlungen, Teilrechnungszahlungen, Teilabstimmung Rechnungszahlungen, Rechnungszahlungen abgleichen, Journaleintrag abgleichen, Journaleinträge abgleichen, Eintrag anpassen, Journaleintrag anpassen, Journaleinträge anpassen, Eintrag anpassen, Rechnung bezahlen, Zahlung für Rechnung mit Rechnung abgleichen, mit Zahlung abgleichen, Rechnung bezahlen, Zahlung für Rechnung mit Rechnung abgleichen, Zahlung in Rechnung abgleichen, Zahlung in Rechnung abgleichen. Automatischer Abgleich Gutschriften mit Rechnung Automatischer Abgleich von Gutschriften mit Rechnung Massenregisterzahlung
     Teilzahlung für Rechnungszeilen Teilzahlung pro Einzelposten Teilzahlung für Rechnungszeile Bezahlen eines Teils einer Rechnungsposition Teilzahlung pro Rechnungszeile Zahlungsverarbeitung auf Zeilenebene Zahlung für bestimmte Rechnungszeilen Teilzahlung für einzelne Posten Zeilenweise Zahlungsverarbeitung Bezahlen bestimmter Posten auf einer Rechnung Rechnungsposition Teilzahlung Teilweise Zahlung von Rechnungspositionen Zahlung für bestimmte Rechnungsprodukte Einzelpostenzahlung auf Rechnungen Teilabrechnung nach Position Selektive Rechnungszahlungen Selektive Zahlung auf Rechnungen Auswahl von Posten für Teilzahlung Teilweise Zahlung ausgewählter Posten Zahlung bestimmter Posten auf Rechnungen Teilabrechnung nach Position Abrechnungsteil einer Rechnungszeile Teilabrechnung für jeden Posten Zahlung auf Zeilenbasis Abrechnung bestimmter Posten auf einer Rechnung Zeilenspezifische Zahlungsvorgänge Zahlungsvorgänge pro Zeile Teilzahlungsvorgänge Verarbeitung von Zahlungen pro Posten Einzelposten-Zahlungsdatensätze Rechnungszeilen-Zahlungszuordnung Zuweisen von Zahlungen auf bestimmte Zeilen Teilzahlungszuordnung Zahlungsverteilung nach Zeile Zuweisung der Zahlung zu einzelnen Posten Einzelpostenrechnungszahlungen Einzelpostenzahlung auf Rechnungen Zahlungsaufschlüsselung nach Zeile Separate Bezahlung bestimmter Posten Teilzahlungsdetails nach Posten Teilzahlungsverfolgung Teilzahlungen Zahlungshistorie nach Zeile Überwachung von Teilzahlungstransaktionen Zahlungsverfolgung für einzelne Posten Rechnungen auf Positionsebene Abrechnung von Rechnungen auf Positionsebene Teilweise Abrechnung pro Position Zahlung auf Rechnungspositionsebene Einzelpositionsabrechnung auf Rechnungen
-----

Aplikasi ini memungkinkan pengguna membayar berdasarkan faktur dan jalur tagihan serta membayar sebagian untuk jalur yang dipilih,
Pembayaran Sebagian melalui jalur Faktur, Pembayaran Sebagian melalui jalur Tagihan,
pembayaran sebagian untuk jalur faktur, pembayaran sebagian untuk jalur tagihan,
Pembayaran melalui jalur faktur, Pembayaran melalui jalur tagihan, pembayaran sebagian,
pembayaran, sebagian, daftarkan pembayaran per baris,
pembayaran sebagian melalui jalur,
pembayaran sebagian melalui jalur inoice, pembayaran sebagian melalui jalur tagihan,
laporan baris berbayar, baris laporan belum dibayar,
baris laporan berbayar belum dibayar,
laporan pembayaran sebagian baris,
daftar pembayaran sebagian, pembayaran Pelanggan,
Faktur pelanggan, Tagihan vendor, pembayaran faktur pelanggan, pembayaran tagihan vendor,
daftarkan pembayaran, pembayaran, sebagian, pelanggan, faktur, Tagihan
laporan berbayar, laporan belum dibayar, laporan pembayaran sebagian,
laporan untuk pembayaran sebagian, laporan pembayaran pelanggan,
pembayaran pelanggan, pembayaran sebagian pelanggan,
pembayaran pelanggan sebagian, dibayar, belum dibayar, daftarkan pembayaran,
baris faktur, baris tagihan, baris pembayaran faktur, baris pembayaran tagihan, baris pembayaran bijaksana,
pembayaran sebagian, laporan pembayaran sebagian, laporan faktur pelanggan, laporan tagihan vendor,
faktur pelanggan, tagihan vendor

pembayaran sebagian dalam faktur pembayaran sebagian dalam tagihan pembayaran sebagian untuk jalur faktur pembayaran sebagian untuk jalur tagihan Pembayaran Banyak Vendor Pembayaran Banyak Tagihan Pembayaran Banyak Pelanggan Pembayaran Banyak Pembayaran Faktur Kredit Catatan beberapa pembayaran merekonsiliasi pembayaran dalam faktur merekonsiliasi pembayaran dalam tagihan Pembayaran faktur sebagian Pembayaran tagihan sebagian Rekonsiliasi sebagian pembayaran faktur rekonsiliasi pembayaran tagihan rekonsiliasi entri jurnal rekonsiliasi entri jurnal rekonsiliasi entri sesuaikan entri jurnal sesuaikan entri jurnal sesuaikan entri Bayar faktur Pembayaran untuk rekonsiliasi faktur dengan faktur rekonsiliasi dengan pembayaran Bayar tagihan Pembayaran rekonsiliasi tagihan dengan rekonsiliasi tagihan rekonsiliasi pembayaran dalam faktur rekonsiliasi pembayaran dalam tagihan Rekonsiliasi Otomatis Nota Kredit dengan Faktur Rekonsiliasi Nota Kredit dengan tagihan Pembayaran Mass Register
     Pembayaran sebagian pada Baris Faktur Pembayaran sebagian berdasarkan item baris Pembayaran sebagian baris faktur Membayar sebagian dari item faktur Pembayaran sebagian per baris faktur Pemrosesan Pembayaran Tingkat Baris Pembayaran pada baris faktur tertentu Pembayaran sebagian untuk masing-masing item Pemrosesan pembayaran berdasarkan garis Membayar item tertentu pada suatu Invoice Item Invoice Pembayaran Sebagian Pembayaran sebagian dari invoice Pembayaran untuk produk invoice tertentu Pembayaran item individual pada invoice Penyelesaian sebagian berdasarkan item Pembayaran Invoice Selektif Pembayaran selektif pada invoice Memilih item untuk pembayaran parsial Membayar sebagian item yang dipilih Pembayaran item tertentu pada invoice Penyelesaian Sebagian berdasarkan Jalur Bagian Penyelesaian dari baris faktur Penyelesaian sebagian untuk setiap item Pembayaran berdasarkan baris demi baris Menyelesaikan item tertentu pada faktur Transaksi Pembayaran Khusus Baris Transaksi pembayaran berdasarkan baris Transaksi pembayaran sebagian Memproses pembayaran berdasarkan item Catatan pembayaran item individual Jalur Faktur Alokasi Pembayaran Mengalokasikan pembayaran ke jalur tertentu Alokasi pembayaran sebagian Distribusi pembayaran per baris Mengalokasikan pembayaran ke masing-masing item Pembayaran Faktur Terperinci Pembayaran terinci pada faktur Rincian pembayaran per baris Membayar item tertentu secara terpisah Rincian pembayaran sebagian per item Pelacakan Pembayaran Sebagian pembayaran parsial Riwayat pembayaran per baris Memantau transaksi pembayaran sebagian Pelacakan pembayaran untuk masing-masing item Line-Level Invoice Menyelesaikan faktur pada tingkat baris Penyelesaian sebagian berdasarkan item baris Pembayaran pada tingkat item faktur Penyelesaian item individual pada faktur
Questa app consente all'utente di pagare tramite fattura e riga di fattura, nonché di pagare parzialmente per le linee selezionate,
Pagamento parziale per righe fattura,Pagamento parziale per righe fattura,
pagamento parziale righe fattura, pagamento parziale righe fattura,
Pagamento per righe fattura, Pagamento per righe fattura, pagamento parziale,
pagamento parziale, registro pagamento per righe,
pagamento parziale per linee,
pagamento parziale per righe fattura, pagamento parziale per righe fattura,
rapporto linee pagate, rapporto linee non pagate,
linee pagate rapporto non pagato,
linee rapporto parziale pagato,
registro dei pagamenti parziali, pagamento del cliente,
Fattura cliente, Fattura fornitore, Pagamento fattura cliente, Pagamento fattura fornitore,
registrare il pagamento,pagamento,parziale,cliente,fattura, fattura
rapporto pagato, rapporto non pagato, rapporto di pagamento parziale,
rapporto per pagamento parziale, rapporto di pagamento del cliente,
pagamento del cliente, pagamento parziale del cliente,
pagamento parziale del cliente, pagato, non pagato, pagamento del registro,
riga fattura,riga fattura,pagamento riga fattura,pagamento riga fattura,pagamento riga,
pagamento parziale, report pagamento parziale, report fattura cliente, report fattura fornitore,
fattura cliente, fattura fornitore

pagamento parziale in fattura pagamento parziale in fattura pagamento parziale per righe fattura pagamento parziale per righe fattura Pagamento multiplo fornitore Pagamento multiplo fattura Pagamento multiplo cliente Pagamento multiplo fattura Note di credito pagamenti multipli riconciliare pagamenti in fattura riconciliare pagamenti in fattura Pagamenti fatture parziali Pagamenti fatture parziali Riconciliazione parziale pagamenti fatture riconciliare pagamenti fatture riconciliare registrazione prima nota riconciliare registrazioni prima nota riconciliare registrazione regolare registrazione prima nota regolare registrazioni prima nota regolare registrazione Pagare fattura Pagamento per fattura riconciliare con fattura riconciliare con pagamento Pagare fattura Pagamento per fattura riconciliare con fattura riconciliare pagamento in fattura riconciliare pagamento in fattura Riconciliazione automatica Note di credito con fattura Riconciliazione automatica Note di credito con fattura Registro di massa Pagamento
     Pagamento parziale su righe fattura Pagamento parziale per voce Pagamento parziale riga fattura Pagamento di parte di una voce fattura Pagamento parziale per riga fattura Elaborazione dei pagamenti a livello di riga Pagamento su righe specifiche della fattura Pagamento parziale per singole voci Elaborazione dei pagamenti per riga Pagamento di voci specifiche su una fattura Articolo fattura Pagamento parziale Pagamento parziale di articoli fattura Pagamento per prodotti fatturati specifici Pagamento di singoli articoli sulle fatture Liquidazione parziale per articolo Pagamenti selettivi delle fatture Pagamento selettivo sulle fatture Scelta di articoli per il pagamento parziale Pagamento parziale di articoli selezionati Pagamento di articoli specifici sulle fatture Liquidazione parziale per riga Parte di liquidazione di una riga della fattura Liquidazione parziale per ogni articolo Pagamento riga per riga Liquidazione di voci specifiche su una fattura Transazioni di pagamento specifiche per riga Transazioni di pagamento per riga Transazioni di pagamento parziali Elaborazione dei pagamenti per voce Record di pagamento di singoli articoli Riga fattura Allocazione pagamento Allocazione pagamento a righe specifiche Allocazione pagamento parziale Distribuzione pagamento per riga Allocazione pagamento a singole voci Pagamenti fatture dettagliate Pagamento dettagliato sulle fatture Suddivisione dei pagamenti per riga Pagamento di articoli specifici separatamente Dettagli pagamento parziale per voce Monitoraggio pagamento parziale pagamenti parziali Cronologia pagamenti per riga Monitoraggio transazioni di pagamento parziali Monitoraggio pagamenti per singoli articoli Fattura a livello di riga Liquidazione delle fatture a livello di riga Liquidazione parziale per voce Pagamento a livello di voce della fattura Liquidazione di singoli articoli sulle fatture

이 앱을 사용하면 사용자는 송장 및 청구서 라인별로 지불할 수 있을 뿐만 아니라 선택한 라인에 대해 부분적으로 지불할 수도 있습니다.
송장 라인별 부분 결제, 빌 라인별 부분 결제,
송장 라인에 대한 부분 지불, 청구서 라인에 대한 부분 지불,
청구서 라인별 결제, 청구서 라인별 결제, 부분 결제,
결제, 부분, 라인별 결제 등록,
라인별 부분결제,
inoice 라인에 의한 부분 지불, 청구 라인에 의한 부분 지불,
라인 지불 보고서, 라인 미지급 보고서,
라인 지불 미지급 보고서,
라인 부분 지급 보고서,
부분결제등록,고객결제,
고객 송장, 공급 업체 청구서, 고객 송장 지불, 공급 업체 청구서 지불,
등록결제,결제,부분,고객,송장,청구서
지급신고, 미지급신고, 부분지급신고,
부분지불 보고서, 고객지불 보고서,
고객결제,고객부분결제,
부분고객결제,유료,미납,등록결제,
송장 라인, 청구서 라인, 송장 라인 지불, 청구서 라인 지불, 라인 현명한 지불,
부분결제,부분결제 보고서,고객 송장 보고서,공급업체 청구서 보고서,
고객 송장, 공급업체 청구서

송장 부분 지급 청구서 부분 지급 inoice 라인에 대한 부분 지급 청구서 라인에 대한 부분 지급 복수 공급업체 지급 복수 청구서 지급 복수 고객 지급 복수 송장 지급 신용 메모 복수 지급 송장 지급 조정 청구서 지급 조정 부분 송장 지급 부분 청구서 지급 부분 조정 송장 지급 조정 청구서 지급 조정 분개 조정 분개 조정 항목 조정 분개 조정 입력 조정 송장 지급 송장 지급 송장과 조정 지급과 조정 청구서 지급 청구서 지급 청구서와 조정 송장에서 지급 조정 청구서에서 지급 조정 자동 조정 송장이 포함된 대변 메모 자동 조정 청구가 포함된 대변 메모 대량 등록 결제
     송장 라인에 대한 부분 지급 개별 항목별 부분 지급 송장 라인 부분 지급 송장 항목의 일부 지급 송장 라인당 부분 지급 라인 수준 지급 처리 특정 송장 라인에 대한 지급 개별 항목에 대한 부분 지급 라인별 지급 처리 특정 항목에 대한 지급 송장 송장 항목 부분 지급 송장 항목 부분 지급 특정 송장 제품에 대한 지급 송장 개별 항목 지급 항목별 부분 정산 선택적 송장 지급 송장 선택적 지급 부분 지급 항목 선택 선택 항목 부분 지급 송장 특정 항목 지급 라인별 부분 정산 부분 정산 항목별 부분정산 라인별 지급 송장 특정항목 정산 라인별 지급거래 라인별 지급거래 부분지급거래 항목별 지급처리 개별항목 지급기록 송장라인 지급할당 지급할당 특정 라인에 부분 지급 할당 라인별 지급 분배 개별 항목에 지급 항목별 송장 지급 송장 항목별 지급 라인별 지급 내역 특정 항목별로 지급 항목별 부분 지급 내역 부분 지급 추적 부분 지급 라인별 지급 내역 부분 지급 거래 모니터링 지급 추적 개별 항목의 경우 라인 수준 송장 라인 수준에서 송장 정산 개별 항목별 부분 정산 송장 항목 수준에서 지급 송장에 대한 개별 항목 정산

このアプリを使用すると、ユーザーは請求書と請求明細によって支払うだけでなく、選択した明細の一部を支払うことができます。
請求書明細による部分支払い、請求書明細による部分支払い、
請求書明細の部分支払い、請求書明細の部分支払い、
請求書明細による支払い、請求書明細による支払い、部分支払い、
支払い、部分的、明細行による支払いの登録、
ラインによる部分支払い、
inoice 行による部分支払い、請求書行による部分支払い、
支払済み明細レポート、未払い明細レポート、
ライン支払済み未払いレポート、
行の部分的な有料レポート、
部分支払い登録、顧客支払い、
顧客請求書、ベンダー請求書、顧客請求書支払い、ベンダー請求書支払い、
支払い、支払い、一部、顧客、請求書、請求書の登録
支払い済みレポート、未払いレポート、部分支払いレポート、
部分支払いレポート、顧客支払いレポート、
顧客の支払い、顧客の一部の支払い、
顧客の一部支払い、支払い済み、未払い、登録支払い、
請求書明細、請求書明細、請求書明細の支払い、請求書明細の支払い、明細ごとの支払い、
部分支払い、部分支払いレポート、顧客請求書レポート、ベンダー請求書レポート、
顧客請求書、ベンダー請求書

請求書での部分支払い 請求書での部分支払い inoice 明細の部分支払い 請求書明細の部分支払い 複数ベンダーの支払い 複数の請求書支払い 複数の顧客の支払い 複数の請求書支払い クレジットノートの複数の支払い 請求書での支払いの調整 請求書での支払いの調整 請求書の一部支払い 請求書の一部支払い 部分的な調整 請求書の支払いを調整します 請求書の支払いを調整します 仕訳入力を調整します 仕訳を調整します 仕訳を調整します 仕訳を調整します 仕訳を調整します 請求書の支払い 請求書の支払い 請求書と調整します 支払いと調整します 請求書の支払い 請求書の支払いを請求書と調整します 請求書での支払いを調整します 請求書での支払いを調整します 自動調整 クレジットノートと請求書を自動照合 クレジットノートと請求書を一括登録 支払いを登録
     請求書明細の部分支払い 明細ごとの部分支払い 請求書明細の部分支払い 請求書明細の一部の支払い 請求書明細ごとの部分支払い 明細レベルの支払い処理 特定の請求書明細の支払い 個別の品目の部分支払い 明細単位の支払い処理 特定の項目の支払い 請求書 請求書項目の部分支払い 請求書項目の一部支払い 特定の請求書商品に対する支払い 請求書の個別項目の支払い 項目別の部分決済 選択的な請求書の支払い 請求書の選択的な支払い 部分支払いの項目の選択 選択した項目の部分的な支払い 請求書の特定の項目の支払い 明細ごとの部分決済 決済部分 請求書明細の部分決済 各品目ごとの部分決済 明細ごとの支払い 請求書の特定品目の決済 品目固有の支払取引 明細ごとの支払取引 部分支払取引 品目ごとの支払いの処理 個別の品目支払記録 請求書明細の支払割り当て 支払いの割り当て 特定の明細への部分的な支払いの割り当て 明細ごとの支払いの配分 個々の項目への支払いの割り当て 請求書支払いの内訳 請求書の支払いの内訳 明細ごとの支払い内訳 特定の項目を個別に支払う 項目ごとの部分的な支払いの詳細 部分的な支払いの追跡 明細ごとの支払い履歴 部分的な支払いトランザクションの監視 支払いの追跡 個別品目の明細レベルの請求書 明細レベルでの請求書の決済 品目別の部分決済 請求書品目レベルでの支払い 請求書の個別品目決済

Este aplicativo permite que o usuário pague por fatura e linha de fatura, bem como pague parcialmente por linhas selecionadas,
Pagamento parcial por linhas de fatura, Pagamento parcial por linhas de fatura,
pagamento parcial para linhas de fatura, pagamento parcial para linhas de fatura,
Pagamento por linhas de fatura, Pagamento por linhas de fatura, pagamento parcial,
pagamento, parcial, cadastrar pagamento por linhas,
pagamento parcial por linhas,
pagamento parcial por linhas de fatura, pagamento parcial por linhas de fatura,
relatório de linhas pagas, relatório de linhas não pagas,
linhas pagas relatório não pago,
linhas relatório pago parcial,
registro de pagamento parcial, pagamento do cliente,
Fatura do cliente, conta do fornecedor, pagamento da fatura do cliente, pagamento da conta do fornecedor,
registrar pagamento, pagamento, parcial, cliente, fatura, fatura
relatório pago, relatório não pago, relatório de pagamento parcial,
relatório para pagamento parcial, relatório de pagamento do cliente,
pagamento do cliente, pagamento parcial do cliente,
pagamento parcial do cliente, pago, não pago, registro de pagamento,
linha de fatura, linha de fatura, pagamento de linha de fatura, pagamento de linha de fatura, pagamento inteligente de linha,
pagamento parcial, relatório de pagamento parcial, relatório de fatura do cliente, relatório de fatura do fornecedor,
fatura do cliente, fatura do fornecedor

pagamento parcial na fatura pagamento parcial na fatura pagamento parcial para linhas de fatura pagamento parcial para linhas de fatura Pagamento de vários fornecedores Pagamento de contas múltiplas Pagamento de vários clientes Pagamento de faturas múltiplas Notas de crédito pagamentos múltiplos reconciliar pagamentos na fatura reconciliar pagamentos na fatura Pagamentos de faturas parciais Pagamentos de contas parciais Reconciliação parcial pagamentos de faturas reconciliar pagamentos de contas reconciliar lançamento contábil manual reconciliar lançamentos contábeis manuais reconciliar entrada ajustar lançamento contábil manual ajustar lançamentos contábeis manuais ajustar entrada Pagar fatura Pagamento de fatura reconciliar com fatura reconciliar com pagamento Pagar fatura Pagamento de fatura reconciliar com fatura reconciliar pagamento na fatura reconciliar pagamento na fatura Reconciliação automática Notas de crédito com fatura Reconciliação automática de notas de crédito com fatura Registro em massa Pagamento
     Pagamento parcial em linhas de fatura Pagamento parcial por item de linha Pagamento parcial de linha de fatura Pagamento parcial de um item de fatura Pagamento parcial por linha de fatura Processamento de pagamento em nível de linha Pagamento em linhas de fatura específicas Pagamento parcial para itens individuais Processamento de pagamento por linha Pagamento de itens específicos em um fatura Item da fatura Pagamento parcial Pagamento parcial de itens da fatura Pagamento de produtos específicos da fatura Pagamento de item individual em faturas Liquidação parcial por item Pagamentos seletivos de faturas Pagamento seletivo em faturas Escolha de itens para pagamento parcial Pagamento parcial de itens selecionados Pagamento de item específico em faturas Liquidação parcial por linha Parte de liquidação de uma linha de fatura Liquidação parcial para cada item Pagamento linha por linha Liquidação de itens específicos em uma fatura Transações de pagamento específicas de linha Transações de pagamento por linha Transações de pagamento parciais Processamento de pagamentos por item Registros de pagamento de item individual Alocação de pagamento de linha de fatura Alocação de pagamento para linhas específicas Alocação de pagamento parcial Distribuição de pagamento por linha Alocação de pagamento para itens individuais Pagamentos de faturas discriminadas Pagamento discriminado em faturas Divisão de pagamento por linha Pagar itens específicos separadamente Detalhes de pagamento parcial por item Pagamento parcial Acompanhamento de pagamentos parciais Histórico de pagamentos por linha Monitoramento de transações de pagamento parcial Acompanhamento de pagamento para itens individuais Fatura em nível de linha Liquidação de faturas em nível de linha Liquidação parcial por item de linha Pagamento no nível de item da fatura Liquidação de item individual em faturas

Это приложение позволяет пользователю оплачивать счета и строки счетов, а также частично оплачивать выбранные строки.
Частичная оплата по строкам счета, Частичная оплата по строкам счета,
частичная оплата по строкам счета, частичная оплата по строкам счета,
Оплата по строкам счета, Оплата по строкам счета, частичная оплата,
оплата, частичная, регистрация оплаты построчно,
частичная оплата построчно,
частичная оплата по строкам счета, частичная оплата по строкам счета,
отчет оплаченных строк, отчет о неоплаченных строках,
строки оплаченного неоплаченного отчета,
частичный платный отчет по строкам,
реестр частичных платежей, оплата клиентов,
Счет-фактура клиента, счет поставщика, оплата счета-фактуры клиента, оплата счета поставщика,
зарегистрировать платеж,оплату,частичный,клиент,счет, счет
оплаченный отчет, неоплаченный отчет, отчет о частичной оплате,
отчет о частичной оплате, отчет о платежах клиентов,
оплата клиента, частичная оплата клиента,
частичная оплата клиента, оплаченная, неоплаченная, регистрация платежа,
строка счета, строка счета, оплата строки счета, оплата строки счета, строка мудрой оплаты,
частичная оплата, отчет о частичной оплате, отчет о счетах клиента, отчет о счетах поставщика,
счет клиента, счет поставщика

Частичная оплата в счете-фактуре Частичная оплата в счете-фактуре Частичная оплата по строкам счета-фактуры Частичная оплата по строкам счета-фактуры Частичная оплата счетов-фактур оплата счетов согласовать оплату счетов согласовать запись в журнале согласовать записи в журнале согласовать запись отрегулировать запись в журнале отрегулировать записи в журнале отрегулировать запись Оплатить счет Оплата по счету согласовать со счетом-фактурой согласовать с оплатой Оплатить счет Оплата по счету согласовать со счетом-фактурой согласовать оплату в счете-фактуре согласовать оплату в счете Автоматическое согласование Кредит-ноты со счетом-фактурой. Автоматическая сверка кредит-нот со счетом. Платеж по массовой регистрации.
     Частичная оплата по строкам счета-фактуры Частичная оплата по позициям Частичная оплата по строке счета-фактуры Оплата части позиции счета-фактуры Частичная оплата по каждой строке счета-фактуры Обработка платежей на уровне строки Оплата по определенным строкам счета-фактуры Частичная оплата по отдельным позициям Построчная обработка платежей Оплата определенных позиций в Позиция счета-фактуры Частичная оплата Частичная оплата позиций счета-фактуры Оплата за определенные продукты счета-фактуры Оплата по отдельным позициям в счетах-фактурах Частичный расчет по позициям Выборочные платежи по счетам-фактурам Выборочная оплата по счетам-фактурам Выбор позиций для частичной оплаты Частичная оплата выбранных позиций Оплата конкретных позиций в счетах-фактурах Частичный расчет по строкам Часть расчета строки счета-фактуры Частичный расчет по каждой позиции Оплата построчно Расчет определенных позиций в счете-фактуре Платежные операции по конкретным строкам Платежные операции по строкам Частичные платежные операции Обработка платежей по позициям Записи об оплате отдельных позиций Распределение платежей по строкам счет-фактуры Распределение платежей Распределение платежей по конкретным строкам Распределение платежей по строкам Распределение платежей по отдельным позициям Детализированные платежи по счетам Детализированные платежи по счетам Разбивка платежей по строкам Оплата конкретных позиций отдельно Детали частичного платежа по позициям Частичные платежи Отслеживание частичных платежей История платежей по строкам Мониторинг транзакций частичных платежей Отслеживание платежей для отдельных позиций Счет на уровне строки Расчет счетов на уровне строки Частичный расчет по отдельной позиции Оплата на уровне позиции позиции счета Расчет по отдельным позициям в счетах-фактурах

Bu uygulama, kullanıcının fatura ve fatura satırına göre ödeme yapmasına ve seçilen hatlar için kısmen ödeme yapmasına olanak tanır,
Fatura Hatlarından Kısmi Ödeme,Fatura Hatlarından Kısmi Ödeme,
Fatura satırlarında kısmi ödeme,Fatura satırlarında kısmi ödeme,
Fatura satırlarıyla ödeme, Fatura satırlarıyla ödeme, Kısmi ödeme,
ödeme, kısmi, hatlarla ödeme kaydı,
hatlarla kısmi ödeme,
Fatura hatları ile kısmi ödeme, Fatura hatları ile kısmi ödeme,
ödenen hatlar raporu, ödenmeyen hatlar raporu,
ödenmiş ödenmemiş hat raporu,
satırlar kısmi ücretli rapor,
kısmi ödeme kaydı, Müşteri ödemesi,
Müşteri faturası, Satıcı faturası, müşteri faturası ödemesi, satıcı faturası ödemesi,
ödemeyi kaydet,ödeme,kısmi,müşteri,fatura, Fatura
ödenmiş rapor, ödenmemiş rapor, kısmi ödeme raporu,
Kısmi ödeme raporu, müşteri ödeme raporu,
müşteri ödemesi, müşteri kısmi ödemesi,
kısmi müşteri ödemesi,ödenmiş,ödenmemiş,kayıt ödemesi,
fatura satırı, fatura satırı, fatura satırı ödemesi, fatura satırı ödemesi, satır bazında ödeme,
kısmi ödeme, kısmi ödeme raporu, müşteri fatura raporu, satıcı fatura raporu,
müşteri faturası, Satıcı faturası

faturada kısmi ödeme Faturada kısmi ödeme Fatura satırları için kısmi ödeme Fatura satırları için kısmi ödeme Çoklu Satıcı Ödemesi Çoklu Fatura Ödemesi Çoklu Müşteri Ödemesi Çoklu Fatura Ödeme Kredi Notları çoklu ödemeler faturadaki ödemelerin mutabakatı faturadaki ödemelerin mutabakatı Kısmi fatura ödemeleri Kısmi fatura ödemeleri Kısmi mutabakat fatura ödemeleri fatura ödemeleri mutabakatı yevmiye kayıtlarını mutabakat yevmiye kayıtlarını mutabakat yevmiye kayıtlarını ayarlamak yevmiye kayıtlarını ayarlamak girişi ayarlamak Fatura ödeme Fatura için ödeme fatura ile mutabakat ödeme ile mutabakat Fatura ödeme Fatura ödemesi fatura ile mutabakat faturada ödeme mutabakatı faturada ödeme mutabakatı Otomatik Mutabakat Faturalı Kredi Dekontları Kredi Dekontlarını faturayla Otomatik Eşitleme Toplu Kayıt Ödemesi
     Fatura Satırlarında Kısmi Ödeme Satır öğesi ile kısmi ödeme Fatura satırı kısmi ödeme Bir fatura kaleminin bir kısmını ödeme Fatura satırı başına kısmi ödeme Satır Düzeyinde Ödeme İşleme Belirli fatura satırlarında ödeme Bireysel kalemler için kısmi ödeme Satır bazında ödeme işleme Belirli kalemleri bir fatura Fatura Kalemi Kısmi Ödeme Fatura kalemlerinin kısmi ödenmesi Belirli fatura ürünleri için ödeme Faturalarda bireysel kalem ödeme Kaleme göre kısmi mahsup Seçmeli Fatura Ödemeleri Faturalarda seçici ödeme Kısmi ödeme için kalemlerin seçilmesi Seçilen kalemlerin kısmen ödenmesi Faturalarda belirli kalem ödemesi Satır bazında kısmi kapatma Mahsup bölümü Her kalem için kısmi kapatma Satır satır ödeme Belirli kalemlerin faturada kapatılması Satıra Özel Ödeme İşlemleri Satır bazında ödeme işlemleri Kısmi ödeme işlemleri Ödemelerin kaleme göre işlenmesi Bireysel kalem ödeme kayıtları Fatura Satırı Ödeme Tahsisi Ödemenin tahsis edilmesi belirli satırlara Kısmi ödeme tahsisi Satır bazında ödeme dağıtımı Ödemenin tek tek öğelere tahsis edilmesi Ayrıntılı Fatura Ödemeleri Faturalarda ayrıntılı ödeme Satır bazında ödeme dökümü Belirli öğelerin ayrı olarak ödenmesi Öğe bazında kısmi ödeme ayrıntıları Kısmi Ödeme Kısmi ödemelerin takibi Satır bazında ödeme geçmişi Kısmi ödeme işlemlerinin izlenmesi Ödeme takibi bireysel kalemler için Satır Düzeyinde Fatura Faturaların satır düzeyinde kapatılması Satır kalemi bazında kısmi kapatma Fatura kalemi düzeyinde ödeme Faturalarda bireysel kalem kapatma

Ця програма дозволяє користувачеві оплачувати за рахунком-фактурою та рядком рахунку, а також частково оплачувати вибрані рядки,
Часткова оплата за рядками рахунку-фактури, часткова оплата за рядками рахунку,
часткова оплата рядків рахунків-фактур, часткова оплата рядків рахунків,
Оплата за рядками рахунків-фактур, Оплата за рядками рахунків, часткова оплата,
оплата, часткова, реєстраційна оплата по рядках,
часткова оплата рядками,
часткова оплата за рядками рахунків, часткова оплата за рядками рахунків,
рядки оплачений звіт, рядки неоплачений звіт,
рядки оплачений неоплачений звіт,
лінії частково оплачений звіт,
реєстр часткових платежів, оплата клієнта,
Рахунок клієнта, рахунок постачальника, оплата рахунку клієнта, оплата рахунку постачальника,
зареєструвати платіж,платіж,частковий,клієнт,рахунок-фактура, рахунок
оплачений звіт, неоплачений звіт, частковий звіт про оплату,
звіт про часткову оплату, звіт про оплату клієнта,
оплата клієнта, часткова оплата клієнта,
часткова оплата клієнта, сплачена, неоплачена, реєстраційна оплата,
рядок рахунків-фактур, рядок рахунків, рядок рахунків-фактур, оплата, рядок рахунків, оплата рядків,
часткова оплата, звіт про часткову оплату, звіт про рахунок клієнта, звіт про рахунок постачальника,
рахунок клієнта, рахунок постачальника

часткова оплата в рахунку-фактурі часткова оплата в рахунку часткова оплата за рядками рахунків часткова оплата за рядками рахунків Платіж кількома постачальниками Платіж кількома рахунками Платіж кількома клієнтами Платіж кількома рахунками-фактурами Кредитні ноти кілька платежів узгодити платежі в рахунку-фактурі узгодити платежі в рахунку Часткові платежі рахунків-фактур Часткові платежі за рахунками Часткове узгодження платежі рахунків-фактур узгодити платежі за рахунками узгодити запис у журналі узгодити записи в журналі узгодити записи в журналі налаштувати записи в журналі налаштувати записи Оплатити рахунок-фактуру Оплата за рахунком-фактурою звірити з рахунком-фактурою звірити з оплатою Оплатити рахунок Оплата за рахунком звірити з рахунком звірити оплату в рахунку-фактурі звірити платіж у рахунку Автоматичне узгодження Кредит-ноти з рахунком-фактурою Автоматичне узгодження кредит-нот з рахунком. Масова реєстрація платежу
     Часткова оплата за рядками рахунків-фактур Часткова оплата за рядками Часткова оплата за рядками рядків рахунків-фактур Оплата частини позицій рахунків-фактур Часткова оплата за рядками рахунків-фактур Обробка платежів на рівні рядків Оплата за окремими рядками рахунків-фактур Часткова оплата для окремих позицій Обробка платежів по рядках Оплата конкретних позицій за рахунок-фактура Позиція рахунка-фактури Часткова оплата Часткова оплата позицій рахунків-фактур Оплата за конкретні продукти рахунків-фактур Оплата окремих позицій за рахунками-фактурами Часткова оплата за позиціями Вибіркові платежі за рахунками-фактурами Вибіркова оплата за рахунками-фактурами Вибір позицій для часткової оплати Часткова оплата вибраних позицій Оплата за окремими позиціями за рахунками-фактурами Часткова оплата за рядками Розрахункова частина рядка рахунка-фактури Частковий розрахунок для кожного елемента Оплата по рядках Розрахунок за конкретними пунктами рахунку-фактури Платіжні транзакції для окремих рядків Платіжні операції за рядками Часткові платіжні транзакції Обробка платежів за елементами Записи платежів за окремими елементами Рядок рахунка-фактури Розподіл платежів Розподіл платежу за певними рядками Частковий розподіл платежів Розподіл платежів за рядками Розподіл платежів за окремими позиціями Деталізовані платежі за рахунками-фактурами Деталізовані платежі за рахунками-фактурами Розподіл платежів за рядками Оплата конкретних позицій окремо Деталі часткового платежу за елементами Відстеження часткових платежів Історія платежів за рядками Моніторинг часткових платіжних операцій Відстеження платежів для окремих позицій Рахунок-фактура на рівні рядка Оплата рахунків-фактур на рівні рядка Частковий розрахунок за позицією рядка Оплата на рівні позиції рахунку-фактури Розрахунок окремої позиції в рахунках-фактурах
Denna app tillåter användare att betala med faktura och fakturarad samt betala delvis för utvalda rader,
Delbetalning med fakturarader, Delbetalning via fakturarader,
delbetalning för fakturarader,delbetalning för fakturarader,
Betalning med fakturarader, Betalning med fakturarader,delbetalning,
betalning, partiell, registrera betalning via rader,
delbetalning via rader,
delbetalning via fakturarader,delbetalning via fakturarader,
rader betalda rapport, rader obetalda rapport,
rader betald obetald rapport,
rader delvis betald rapport,
delbetalningsregister,Kundbetalning,
Kundfaktura, leverantörsfaktura, kundfakturabetalning, betalning av leverantörsfaktura,
registrera betalning, betalning, partiell, kund, faktura, räkning
betald rapport,obetald rapport,delbetalningsrapport,
rapport för delbetalning, kundbetalningsrapport,
kundbetalning, kunddelbetalning,
partiell kundbetalning, betald, obetald, registrera betalning,
fakturarad, fakturarad, fakturaradsbetalning, fakturaradsbetalning, linjevis betalning,
delbetalning, delbetalningsrapport, kundfakturarapport, leverantörsfakturarapport,
kundfaktura, leverantörsräkning

delbetalning i faktura delbetalning i Faktura delbetalning för fakturarader delbetalning för fakturarader Flera leverantörsbetalningar Flera fakturabetalningar Flera kundbetalningar Flera fakturabetalningar Kreditnotor flera betalningar stämmer av betalningar i faktura stämmer av betalningar i faktura Delfakturabetalningar Delfakturabetalningar Delvis avstämning fakturabetalningar stämma av fakturabetalningar stämma av journalanteckning stämma av journalanteckningar stämma av journalposter justera journalanteckning justera journalanteckningar justera post Betala faktura Betalning för faktura stämma av med faktura stämma av med betalning Betala räkning Betalning för räkning stämma av mot räkning Autostämma betalning i faktura stämma av Kreditnotor med faktura Automatisk avstämning av kreditnotor med fakturamassregisterbetalning
     Delbetalning på fakturarader Delbetalning per rad Fakturarad delbetalning Betalning av del av en fakturapost Delbetalning per fakturarad Betalningshantering på radnivå Betalning på specifika fakturarader Delbetalning för enskilda poster Radvis betalningshantering Betalning av specifika poster på en faktura Fakturapost Delbetalning Delbetalning av fakturaartiklar Betalning för specifika fakturaprodukter Enskild artikelbetalning på faktura Delavräkning per post Selektiv fakturabetalning Selektiv betalning på faktura Välja poster för delbetalning Delbetalning av utvalda poster Specifik artikelbetalning på faktura Delavräkning per radavräkningsdel av en fakturarad Delavräkning för varje artikel Betalning rad för rad Avräkning av specifika poster på en faktura Radspecifika betalningstransaktioner Betalningstransaktioner per rad Delbetalningstransaktioner Bearbetning av betalningar per artikel Betalningsposter för individuella poster Fakturarad Betalningsfördelning Allokera betalning till specifika rader Delbetalningsfördelning Betalningsfördelning per rad Fördelning av betalning till enskilda poster Specificerade fakturabetalningar Specificerade betalningar på fakturor Betalningsfördelning per rad Betalning av specifika poster separat Delbetalningsinformation per post Delbetalningsspårning av delbetalningar Betalningshistorik per rad Övervaka delbetalningstransaktioner Betalningsspårning för enskilda poster Faktura på radnivå Avräkning av fakturor på radnivå Delavräkning per rad Betalning på fakturapostnivå Individuell artikelavräkning på fakturor
يتيح هذا التطبيق للمستخدم الدفع عن طريق الفاتورة وخط الفاتورة وكذلك الدفع جزئيًا للخطوط المحددة،
الدفع الجزئي عن طريق خطوط الفاتورة، الدفع الجزئي عن طريق خطوط الفاتورة،
الدفع الجزئي لخطوط الفاتورة، الدفع الجزئي لخطوط الفاتورة،
الدفع عن طريق خطوط الفاتورة، الدفع عن طريق خطوط الفاتورة، الدفع الجزئي،
الدفع، الجزئي، تسجيل الدفع عن طريق الخطوط،
الدفع الجزئي عن طريق الخطوط،
الدفع الجزئي عن طريق خطوط inoice، الدفع الجزئي عن طريق خطوط الفاتورة،
تقرير الخطوط المدفوعة، تقرير الخطوط غير المدفوعة،
تقرير الخطوط المدفوعة غير المدفوعة,
خطوط تقرير مدفوع جزئيًا,
سجل الدفع الجزئي، دفع العملاء،
فاتورة العميل، فاتورة البائع، دفع فاتورة العميل، دفع فاتورة البائع،
تسجيل الدفع، الدفع، الجزئي، العميل، الفاتورة، الفاتورة
تقرير مدفوع، تقرير غير مدفوع، تقرير دفع جزئي،
تقرير الدفع الجزئي، تقرير دفع العملاء،
دفع العميل ، الدفع الجزئي للعميل ،
الدفع الجزئي للعملاء، المدفوعة، غير المدفوعة، تسجيل الدفع،
سطر الفاتورة، سطر الفاتورة، دفع سطر الفاتورة، دفع سطر الفاتورة، خط الدفع الحكيم،
الدفع الجزئي، تقرير الدفع الجزئي، تقرير فاتورة العميل، تقرير فاتورة البائع،
فاتورة العميل، فاتورة البائع

السداد الجزئي في الفاتورة السداد الجزئي في الفاتورة السداد الجزئي لخطوط inoice السداد الجزئي لخطوط الفاتورة دفع البائعين المتعددين دفع الفواتير المتعددة دفع العملاء المتعددين دفع الفواتير المتعددة الإشعارات الائتمانية الدفعات المتعددة تسوية المدفوعات في الفاتورة تسوية المدفوعات في الفاتورة مدفوعات الفاتورة الجزئية مدفوعات الفواتير الجزئية تسوية جزئية تسوية مدفوعات الفواتير تسوية مدفوعات الفواتير تسوية قيد اليومية تسوية إدخالات دفتر اليومية تسوية القيد ضبط قيد اليومية ضبط قيود اليومية ضبط الإدخال دفع الفاتورة الدفع لتسوية الفاتورة مع تسوية الفاتورة مع الدفع دفع الفاتورة الدفع لتسوية الفاتورة مع تسوية الفاتورة الدفع في الفاتورة تسوية الدفع في الفاتورة التسوية التلقائية إشعارات الائتمان مع الفاتورة التسوية التلقائية لملاحظات الائتمان مع الدفع الجماعي للفاتورة
     الدفع الجزئي على بنود الفاتورة الدفع الجزئي حسب عنصر السطر الدفع الجزئي لسطر الفاتورة دفع جزء من عنصر الفاتورة الدفع الجزئي لكل سطر فاتورة معالجة الدفع على مستوى الخط الدفع على بنود فاتورة محددة الدفع الجزئي للعناصر الفردية معالجة الدفع حسب الخط دفع عناصر محددة على فاتورة عنصر الفاتورة الدفع الجزئي لعناصر الفاتورة سداد جزئي لعناصر الفاتورة الدفع لمنتجات فاتورة محددة دفع عنصر فردي على الفواتير تسوية جزئية حسب العنصر مدفوعات الفاتورة الانتقائية دفع انتقائي على الفواتير اختيار عناصر للدفع الجزئي دفع جزئي لعناصر مختارة دفع عنصر محدد على الفواتير التسوية الجزئية عن طريق الخط تسوية جزء لبند فاتورة تسوية جزئية لكل عنصر الدفع على أساس كل سطر تسوية بنود محددة في فاتورة معاملات الدفع الخاصة بكل سطر معاملات الدفع حسب السطر معاملات الدفع الجزئي معالجة المدفوعات حسب العنصر سجلات دفع العنصر الفردي تخصيص الدفع لخط الفاتورة تخصيص الدفع لخطوط محددة تخصيص الدفع الجزئي توزيع الدفع حسب الخط تخصيص الدفع للعناصر الفردية مدفوعات الفاتورة المفصلة الدفع المفصل على الفواتير تفاصيل الدفع حسب الخط دفع عناصر محددة بشكل منفصل تفاصيل الدفع الجزئي حسب العنصر تتبع الدفع الجزئي المدفوعات الجزئية سجل الدفع حسب السطر مراقبة معاملات الدفع الجزئي تتبع الدفع للعناصر الفردية الفاتورة على مستوى البند تسوية الفواتير على مستوى البند التسوية الجزئية حسب البند الدفع على مستوى عنصر الفاتورة تسوية العنصر الفردي على الفواتير

این برنامه به کاربر اجازه می دهد تا از طریق فاکتور و خط قبض و همچنین پرداخت جزئی برای خطوط انتخاب شده، پرداخت کند.
پرداخت جزئی از طریق خطوط فاکتور، پرداخت جزئی توسط خطوط قبض،
پرداخت جزئی برای خطوط فاکتور، پرداخت جزئی برای خطوط صورتحساب،
پرداخت از طریق خطوط فاکتور، پرداخت از طریق خطوط قبض، پرداخت جزئی،
پرداخت، جزئی، ثبت پرداخت از طریق خطوط،
پرداخت جزئی از طریق خطوط،
پرداخت جزئی توسط خطوط inoice، پرداخت جزئی توسط خطوط قبض،
گزارش پرداختی خطوط، گزارش پرداخت نشده خطوط،
خطوط پرداختی گزارش پرداخت نشده،
خطوط گزارش پرداخت جزئی،
ثبت پرداخت جزئی، پرداخت مشتری،
فاکتور مشتری، قبض فروشنده، پرداخت فاکتور مشتری، پرداخت قبض فروشنده،
ثبت پرداخت، پرداخت، جزئی، مشتری، فاکتور، قبض
گزارش پرداخت شده، گزارش پرداخت نشده، گزارش پرداخت جزئی،
گزارش پرداخت جزئی، گزارش پرداخت مشتری،
پرداخت مشتری، پرداخت جزئی مشتری،
پرداخت جزئی مشتری، پرداخت شده، پرداخت نشده، پرداخت ثبت نام،
خط فاکتور، خط قبض، پرداخت خط فاکتور، پرداخت خط قبض، پرداخت خطی،
پرداخت جزئی، گزارش پرداخت جزئی، گزارش فاکتور مشتری، گزارش قبض فروشنده،
فاکتور مشتری، قبض فروشنده

پرداخت جزئی در فاکتور پرداخت جزئی در قبض پرداخت جزئی برای خطوط فاکتور پرداخت جزئی برای خطوط قبض پرداخت چند فروشنده پرداخت قبض چندگانه پرداخت چند قبض پرداخت چندگانه توسط مشتری پرداخت چند قبض اعتبار یادداشت‌های اعتباری پرداخت‌های چندگانه تطبیق پرداخت‌ها در صورت‌حساب تطبیق پرداخت‌ها در صورتحساب پرداخت‌های فاکتور جزئی پرداخت قبض جزئی پرداخت صورتحساب تطبیق پرداخت صورتحساب تطبیق ورود دفترچه ثبت تطبیق مدخل های مجله تطبیق ورود تنظیم دفترچه ثبت دفتر تنظیم دفترچه یادداشت تنظیم ورودی پرداخت فاکتور پرداخت برای فاکتور تطبیق با فاکتور تطبیق با پرداخت پرداخت صورتحساب پرداخت برای تطبیق صورتحساب تطبیق خودکار با صورتحساب تطبیق پرداخت در صورتحساب یادداشت های اعتباری با فاکتور تطبیق خودکار یادداشت های اعتباری با قبض پرداخت ثبت نام انبوه
     پرداخت جزئی در خطوط فاکتور پرداخت جزئی توسط خط فاکتور پرداخت جزئی خط فاکتور پرداخت جزئی از یک قلم فاکتور پرداخت جزئی به ازای هر خط فاکتور پردازش پرداخت در سطح خط پرداخت پرداخت در خطوط فاکتور خاص پرداخت جزئی برای موارد جداگانه پردازش خطی پرداخت پرداخت اقلام خاص در یک فاکتور مورد فاکتور پرداخت جزئی پرداخت جزئی اقلام فاکتور پرداخت جزئی اقلام فاکتور پرداخت برای محصولات فاکتور خاص پرداخت اقلام انفرادی بر روی فاکتورها تسویه جزئی بر اساس مورد پرداخت فاکتور انتخابی پرداخت انتخابی روی فاکتورها انتخاب اقلام برای پرداخت جزئی پرداخت جزئی موارد انتخاب شده پرداخت اقلام خاص روی فاکتورها تسویه جزئی توسط تسویه خطی یک خط فاکتور تسویه جزئی برای هر کالا پرداخت به صورت خط به خط تسویه اقلام خاص بر روی یک فاکتور معاملات پرداخت خطی خاص تراکنش های پرداخت بر اساس خط تراکنش های پرداخت جزئی پردازش پرداخت ها بر اساس کالا سوابق پرداخت اقلام جداگانه خط فاکتور پرداخت تخصیص تخصیص پرداخت به خطوط خاص تخصیص پرداخت جزئی توزیع پرداخت بر اساس خط تخصیص پرداخت به اقلام جداگانه پرداخت فاکتورهای تفکیک شده پرداخت بر اساس فاکتورها تفکیک پرداخت بر اساس خط پرداخت اقلام خاص به طور جداگانه جزئیات پرداخت جزئی بر اساس مورد پیگیری پرداخت جزئی پیگیری پرداخت های جزئی سابقه پرداخت بر اساس خط نظارت بر تراکنش های پرداخت جزئی پیگیری پرداخت برای اقلام جداگانه صورتحساب در سطح خط تسویه فاکتورها در سطح خط تسویه جزئی توسط اقلام خطی پرداخت در سطح اقلام فاکتور تسویه اقلام انفرادی روی فاکتورها


	 """,
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:        
