import json
import os

from dotenv import load_dotenv
from openai import OpenAI

from src.utils import check_connections, get_expense_extraction_prompt

load_dotenv()

def test_deepseek_connection(custom_email=None):
    if not check_connections():
        return

    api_key = os.getenv("DEEPSEEK_API_KEY")
    base_url = os.getenv("DEEPSEEK_BASE_URL")
    model = os.getenv("DEEPSEEK_MODEL")

    client = OpenAI(api_key=api_key, base_url=base_url)

    if custom_email:
        print(f"🚀 Testing expense extraction from custom email using {model}...")
        prompt = get_expense_extraction_prompt(custom_email)
        
        try:
            response = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": "You are a helpful assistant that extracts expense data from emails into JSON."},
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"}
            )
            print("\n✅ Success! Extracted JSON:")
            print(json.dumps(json.loads(response.choices[0].message.content), indent=2))
        except Exception as e:
            print(f"\n❌ Extraction failed: {e}")
    else:
        print(f"🚀 Testing simple connection to DeepSeek at {base_url} using {model}...")
        try:
            response = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "user", "content": "Say 'Hello World! DeepSeek connection is working.'"}
                ],
                stream=False
            )
            print("\n✅ Success! Response:")
            print(response.choices[0].message.content)
        except Exception as e:
            print(f"\n❌ Connection failed: {e}")

PAYMENT_EMAIL = """From: davivienda_notifica@davivienda.com.sv
Date: 2026-10-01 17:06:22
Subject: Notificacion

Content:
Estimado(a) Cliente: CLIENTE DE PRUEBA
Le notificamos que su cuenta ****0000 ha sido cargada cuyos detalles se
muestran a continuacion: Propietario Cta. Destino : ****** En concepto de
: PAGO DE TARJETA DE CREDITO Fecha y Hora : 01/10/26 11:06:44 AM Numero de
confirmacion : 0 Monto : 12.20 NOTA: Si no ha sido realizada por usted,
llamar de inmediato al 2556-0000"""

PURCHASE_EMAIL = """From: davivienda_notifica@davivienda.com.sv
Date: 2026-09-23 19:46:11
Subject: Notificacion

Content:
Estimado(a) cliente de Banco Davivienda: Le informamos que su Tarjeta de
Credito: 0000 fue Cargada. A continuacion el detalle: Monto de transaccion /
moneda: 12.20 USD Nombre del comercio: CLOUDFLARE Fecha: 23/09/2026
19:46:11 Localizacion del comercio: ESTADOS UNIDOS DE AMERICA"""


def test_is_expense_classification():
    """A payment must be is_expense=false; a real purchase must be true."""
    from src.ai_service import extract_expense_from_email

    payment = extract_expense_from_email(PAYMENT_EMAIL)
    purchase = extract_expense_from_email(PURCHASE_EMAIL)
    print("\npayment :", json.dumps(payment, indent=2))
    print("purchase:", json.dumps(purchase, indent=2))
    assert payment.get("is_expense") is False, payment
    assert purchase.get("is_expense") is True, purchase
    print("\n✅ Classification self-test ok")


if __name__ == "__main__":
    # Test with the specific email provided by the user if requested
    import sys as system_sys
    if len(system_sys.argv) > 1 and system_sys.argv[1] == "--classify":
        test_is_expense_classification()
    elif len(system_sys.argv) > 1 and system_sys.argv[1] == "--email":
        sample_email = """From: notificaciones@bancocuscatlan.com 
Date: 2026-04-29 21:24:00
Subject: Compra con Tarjeta de Credito Titular 

Content: 
1213 
Estimado Cliente: CLIENTE DE PRUEBA
Se ha realizado una compra con su tarjeta titular de Banco CUSCATLAN XXXXXXXXXX0000 por USD 5.30 en DeepSeek el día 2026-04-29 21:24. Consultas al 22122000."""
        test_deepseek_connection(custom_email=sample_email)
    else:
        test_deepseek_connection()
