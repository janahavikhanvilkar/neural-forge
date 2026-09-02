import os
import re
import json
import requests

from config import Config


class AIService:

    def __init__(self):
        self.api_key = os.getenv("GEMINI_API_KEY") or Config.GEMINI_API_KEY
        self.client = None
        self._init_client()

    # =========================================================================
    # GEMINI INITIALIZATION
    # =========================================================================

    def _init_client(self):
        if self.api_key and self.api_key.strip():
            try:
                from google import genai

                self.client = genai.Client(
                    api_key=self.api_key.strip()
                )

            except Exception as e:
                print(
                    f"Warning: Google GenAI client initialization failed: {e}"
                )
                self.client = None

    # =========================================================================
    # GEMINI API CALL
    # =========================================================================

    def call_gemini(
        self,
        prompt: str,
        system_instruction: str = None
    ) -> str:
        """
        Calls Google Gemini API.
        Uses SDK first and REST API as fallback.
        """

        if not self.api_key or not self.api_key.strip():
            return None

        # ---------------------------------------------------------------------
        # SDK
        # ---------------------------------------------------------------------

        if self.client:

            try:
                model_name = "gemini-2.5-flash"

                config = None

                if system_instruction:
                    config = {
                        "system_instruction": system_instruction,
                        "temperature": 0.1,
                        "top_p": 0.8,
                    }

                response = self.client.models.generate_content(
                    model=model_name,
                    contents=prompt,
                    config=config
                )

                if response and response.text:
                    return response.text.strip()

            except Exception as e:

                print(
                    f"Gemini SDK call error: {e}, "
                    f"attempting REST fallback..."
                )

        # ---------------------------------------------------------------------
        # REST FALLBACK
        # ---------------------------------------------------------------------

        try:

            url = (
                "https://generativelanguage.googleapis.com/"
                "v1beta/models/gemini-2.5-flash:generateContent"
                f"?key={self.api_key.strip()}"
            )

            headers = {
                "Content-Type": "application/json"
            }

            final_prompt = prompt

            if system_instruction:
                final_prompt = (
                    f"SYSTEM INSTRUCTION:\n"
                    f"{system_instruction}\n\n"
                    f"USER TASK:\n"
                    f"{prompt}"
                )

            payload = {
                "contents": [
                    {
                        "parts": [
                            {
                                "text": final_prompt
                            }
                        ]
                    }
                ],
                "generationConfig": {
                    "temperature": 0.1,
                    "topP": 0.8,
                    "responseMimeType": "application/json"
                }
            }

            resp = requests.post(
                url,
                headers=headers,
                json=payload,
                timeout=30
            )

            if resp.status_code == 200:

                data = resp.json()

                candidates = data.get("candidates", [])

                if candidates:

                    content = candidates[0].get("content", {})

                    parts = content.get("parts", [])

                    if parts:

                        text = parts[0].get("text")

                        if text:
                            return text.strip()

            else:

                print(
                    f"Gemini REST error: "
                    f"{resp.status_code} - {resp.text}"
                )

        except Exception as ex:

            print(
                f"Gemini REST Exception: {ex}"
            )

        return None

    # =========================================================================
    # JSON CLEANER
    # =========================================================================

    def _clean_json_response(self, text: str) -> dict:
        """
        Safely extracts JSON from Gemini response.
        """

        if not text:
            return {}

        try:

            clean = text.strip()

            # Remove markdown code block
            clean = re.sub(
                r"^```(?:json)?\s*",
                "",
                clean,
                flags=re.IGNORECASE
            )

            clean = re.sub(
                r"\s*```$",
                "",
                clean
            )

            clean = clean.strip()

            # Try direct JSON first
            try:
                return json.loads(clean)
            except Exception:
                pass

            # Find JSON object
            match = re.search(
                r"\{.*\}",
                clean,
                re.DOTALL
            )

            if match:

                json_text = match.group(0)

                return json.loads(json_text)

        except Exception as e:

            print(
                f"JSON parsing error: {e} "
                f"in text: {text[:300]}"
            )

        return {}

    # =========================================================================
    # INVOICE HELPERS
    # =========================================================================

    def _extract_invoice_number(self, text: str) -> str:
        """
        Extract invoice number only from clearly labelled fields.
        Prevents values such as 'Invoice' from being returned.
        """

        patterns = [

            r"\binvoice\s*(?:number|no\.?|#)\s*[:\-]?\s*"
            r"([A-Z0-9][A-Z0-9_\-/]+)",

            r"\binvoice\s*[:\-]?\s*"
            r"([A-Z]{2,}[-_/]?\d[\w\-/]+)",

            r"\binv\.?\s*(?:number|no\.?|#)?\s*[:\-]?\s*"
            r"([A-Z0-9][A-Z0-9_\-/]+)",
        ]

        for pattern in patterns:

            match = re.search(
                pattern,
                text,
                re.IGNORECASE
            )

            if match:

                value = match.group(1).strip()

                # Reject generic words
                if value.lower() not in {
                    "invoice",
                    "number",
                    "no",
                    "none",
                    "null"
                }:

                    return value

        return ""

    def _extract_labeled_value(
        self,
        text: str,
        labels: list
    ) -> str:
        """
        Extracts a value appearing after a label.
        """

        for label in labels:

            pattern = (
                rf"(?im)^\s*{label}\s*"
                r"[:#\-]?\s*(.+?)\s*$"
            )

            match = re.search(
                pattern,
                text
            )

            if match:

                value = match.group(1).strip()

                if value:
                    return value

        return ""

    def _extract_invoice_dates(self, text: str):
        """
        Extracts invoice date and due date using their labels.
        """

        date_pattern = (
            r"(?:"
            r"\d{4}[-/.]\d{1,2}[-/.]\d{1,2}"
            r"|"
            r"\d{1,2}[-/.]\d{1,2}[-/.]\d{2,4}"
            r"|"
            r"[A-Za-z]{3,9}\s+\d{1,2},?\s+\d{4}"
            r")"
        )

        invoice_date = ""
        due_date = ""

        # Invoice date
        invoice_patterns = [

            rf"(?im)^\s*(?:invoice\s+)?date\s*[:\-]?\s*"
            rf"({date_pattern})",

            rf"(?im)^\s*date\s*[:\-]?\s*"
            rf"({date_pattern})",
        ]

        for pattern in invoice_patterns:

            match = re.search(
                pattern,
                text
            )

            if match:

                invoice_date = match.group(1).strip()
                break

        # Due date
        due_patterns = [

            rf"(?im)^\s*due\s+date\s*[:\-]?\s*"
            rf"({date_pattern})",

            rf"(?im)^\s*payment\s+due\s*[:\-]?\s*"
            rf"({date_pattern})",
        ]

        for pattern in due_patterns:

            match = re.search(
                pattern,
                text
            )

            if match:

                due_date = match.group(1).strip()
                break

        return invoice_date, due_date

    def _extract_money_after_label(
        self,
        text: str,
        labels: list
    ):
        """
        Extracts numeric money value from a labelled field.

        Example:
        Subtotal: ₹5,633.00
        Sales Tax (8%): ₹400.00
        Total Due: ₹6,033.00
        """

        number_pattern = (
            r"(?:[$€£₹]\s*)?"
            r"([\d,]+(?:\.\d{1,2})?)"
        )

        for label in labels:

            pattern = (
                rf"(?im)^\s*{label}"
                rf"(?:\s*\([^)]*\))?"
                rf"\s*[:\-]?\s*"
                rf"{number_pattern}"
            )

            match = re.search(
                pattern,
                text
            )

            if match:

                try:

                    return float(
                        match.group(1).replace(",", "")
                    )

                except ValueError:
                    pass

        return None

    def _detect_currency(self, text: str) -> str:
        """
        Detects invoice currency from symbols or currency names.
        """

        text_lower = text.lower()

        if "₹" in text or "inr" in text_lower:
            return "INR"

        if "$" in text or "usd" in text_lower:
            return "USD"

        if "€" in text or "eur" in text_lower:
            return "EUR"

        if "£" in text or "gbp" in text_lower:
            return "GBP"

        return "USD"

    def _extract_vendor(self, text: str) -> str:
        """
        Extract vendor/company name without accidentally returning
        Subtotal, Invoice, Date, etc.
        """

        lines = [
            line.strip()
            for line in text.splitlines()
            if line.strip()
        ]

        # ---------------------------------------------------------------------
        # First: explicitly labelled vendor fields
        # ---------------------------------------------------------------------

        vendor_labels = [
            "vendor",
            "vendor name",
            "seller",
            "seller name",
            "supplier",
            "supplier name",
            "company",
            "company name",
            "from"
        ]

        for label in vendor_labels:

            match = re.search(
                rf"(?im)^\s*{label}\s*[:\-]?\s*(.+?)\s*$",
                text
            )

            if match:

                value = match.group(1).strip()

                if self._is_valid_vendor(value):
                    return value

        # ---------------------------------------------------------------------
        # Second: inspect first 10 lines
        # ---------------------------------------------------------------------

        invalid_words = [
            "subtotal",
            "tax",
            "gst",
            "total",
            "amount",
            "invoice",
            "date",
            "due date",
            "bill to",
            "billed to",
            "customer",
            "description",
            "quantity",
            "price",
            "payment",
            "terms",
            "email",
            "phone",
            "address"
        ]

        for line in lines[:10]:

            line_lower = line.lower()

            if any(
                word in line_lower
                for word in invalid_words
            ):
                continue

            # Skip pure numbers
            if re.fullmatch(
                r"[\d\s.,₹$€£:/#\-]+",
                line
            ):
                continue

            # Skip email
            if "@" in line:
                continue

            if self._is_valid_vendor(line):
                return line

        return ""

    def _is_valid_vendor(self, value: str) -> bool:
        """
        Checks whether a string looks like a vendor name.
        """

        if not value:
            return False

        value = value.strip()

        if len(value) < 2:
            return False

        lower = value.lower()

        bad_starts = [
            "subtotal",
            "tax",
            "gst",
            "total",
            "total due",
            "amount due",
            "invoice",
            "invoice number",
            "date",
            "due date",
            "bill to",
            "billed to",
            "customer",
            "description",
            "quantity",
            "unit price",
            "payment"
        ]

        if any(
            lower.startswith(x)
            for x in bad_starts
        ):
            return False

        if "@" in value:
            return False

        return True

    def _extract_customer(self, text: str) -> str:
        """
        Extract customer/billed-to information.
        """

        patterns = [

            r"(?im)^\s*bill\s+to\s*[:\-]?\s*(.+?)\s*$",

            r"(?im)^\s*billed\s+to\s*[:\-]?\s*(.+?)\s*$",

            r"(?im)^\s*customer\s*[:\-]?\s*(.+?)\s*$",

            r"(?im)^\s*client\s*[:\-]?\s*(.+?)\s*$",

            r"(?im)^\s*sold\s+to\s*[:\-]?\s*(.+?)\s*$",
        ]

        for pattern in patterns:

            match = re.search(
                pattern,
                text
            )

            if match:

                value = match.group(1).strip()

                if value:
                    return value

        return ""

    def _validate_invoice_data(
        self,
        extracted: dict,
        raw_text: str
    ) -> dict:
        """
        Critical post-processing step.

        Gemini may understand the invoice but occasionally place
        extracted values in the wrong JSON fields.

        This method compares Gemini output against explicit labels
        found in the original invoice text.
        """

        text = raw_text or ""

        # ---------------------------------------------------------------------
        # Vendor
        # ---------------------------------------------------------------------

        vendor_from_text = self._extract_vendor(text)

        if vendor_from_text:

            current_vendor = str(
                extracted.get("vendor", "")
            ).strip()

            # Replace obviously incorrect vendor
            if (
                not current_vendor
                or
                not self._is_valid_vendor(current_vendor)
                or
                current_vendor.lower() in {
                    "invoice",
                    "subtotal",
                    "total",
                    "date",
                    "due date"
                }
            ):
                extracted["vendor"] = vendor_from_text

        # ---------------------------------------------------------------------
        # Invoice Number
        # ---------------------------------------------------------------------

        invoice_number = self._extract_invoice_number(text)

        if invoice_number:

            extracted["invoice_number"] = invoice_number

        # ---------------------------------------------------------------------
        # Customer
        # ---------------------------------------------------------------------

        customer = self._extract_customer(text)

        if customer:

            extracted["customer_name"] = customer

        # ---------------------------------------------------------------------
        # Dates
        # ---------------------------------------------------------------------

        invoice_date, due_date = self._extract_invoice_dates(text)

        if invoice_date:
            extracted["invoice_date"] = invoice_date

        if due_date:
            extracted["due_date"] = due_date

        # ---------------------------------------------------------------------
        # Currency
        # ---------------------------------------------------------------------

        extracted["currency"] = self._detect_currency(text)

        # ---------------------------------------------------------------------
        # Subtotal
        # ---------------------------------------------------------------------

        subtotal = self._extract_money_after_label(
            text,
            [
                r"subtotal",
                r"sub\s*total",
                r"net\s+amount"
            ]
        )

        if subtotal is not None:
            extracted["subtotal"] = subtotal

        # ---------------------------------------------------------------------
        # Tax
        # ---------------------------------------------------------------------

        tax = self._extract_money_after_label(
            text,
            [
                r"sales\s+tax",
                r"tax",
                r"gst",
                r"vat"
            ]
        )

        if tax is not None:
            extracted["tax"] = tax

        # ---------------------------------------------------------------------
        # Total
        # ---------------------------------------------------------------------

        total = self._extract_money_after_label(
            text,
            [
                r"total\s+amount\s+due",
                r"total\s+due",
                r"total\s+amount",
                r"amount\s+due",
                r"balance\s+due",
                r"grand\s+total",
                r"total"
            ]
        )

        if total is not None:
            extracted["total"] = total

        # ---------------------------------------------------------------------
        # Convert numbers
        # ---------------------------------------------------------------------

        for field in [
            "subtotal",
            "tax",
            "total"
        ]:

            try:

                value = extracted.get(field, 0)

                if value is None or value == "":
                    value = 0

                if isinstance(value, str):

                    value = (
                        value
                        .replace(",", "")
                        .replace("₹", "")
                        .replace("$", "")
                        .replace("€", "")
                        .replace("£", "")
                        .strip()
                    )

                extracted[field] = round(
                    float(value),
                    2
                )

            except Exception:

                extracted[field] = 0.0

        # ---------------------------------------------------------------------
        # Math validation
        # ---------------------------------------------------------------------

        subtotal = extracted["subtotal"]
        tax = extracted["tax"]
        total = extracted["total"]

        flags = []

        expected_total = round(
            subtotal + tax,
            2
        )

        if (
            subtotal > 0
            and tax >= 0
            and total > 0
        ):

            difference = abs(
                expected_total - total
            )

            if difference > 0.05:

                flags.append(
                    "Math discrepancy: "
                    f"Subtotal ({subtotal:.2f}) + "
                    f"Tax ({tax:.2f}) != "
                    f"Total ({total:.2f})"
                )

        if not extracted.get("invoice_number"):
            flags.append(
                "Invoice number not clearly found"
            )

        if not extracted.get("vendor"):
            flags.append(
                "Vendor name not clearly found"
            )

        if not extracted.get("customer_name"):
            flags.append(
                "Customer / Billed To not clearly found"
            )

        if not extracted.get("invoice_date"):
            flags.append(
                "Invoice date not clearly found"
            )

        if not extracted.get("due_date"):
            flags.append(
                "Due date not clearly found"
            )

        if not extracted.get("payment_info"):
            extracted["payment_info"] = "Not specified"

        if not flags:

            extracted["validation_flags"] = [
                "All validation checks passed"
            ]

        else:

            extracted["validation_flags"] = flags

        # ---------------------------------------------------------------------
        # Confidence
        # ---------------------------------------------------------------------

        confidence = 95

        confidence -= min(
            len(flags) * 5,
            30
        )

        confidence = max(
            20,
            min(confidence, 99)
        )

        extracted["confidence"] = confidence

        extracted["reasoning"] = (
            "Invoice data extracted using Gemini AI and "
            "validated against explicitly labelled values "
            "in the original invoice text."
        )

        return extracted

    # =========================================================================
    # 1. INVOICE PROCESSING
    # =========================================================================

    def extract_invoice_data(
        self,
        raw_text: str,
        filename: str = ""
    ) -> dict:

        """
        Extracts invoice data using Gemini and performs
        deterministic validation against the original text.
        """

        if not raw_text:
            return self._heuristic_invoice_extraction(
                "",
                filename
            )

        prompt = f"""
You are an expert financial auditor and document extraction AI.

Your task is to extract invoice information EXACTLY from the
provided invoice text.

IMPORTANT RULES:

1. Never move a value into another field.
2. Never guess a value that is not present.
3. Do NOT use examples from this prompt as actual invoice data.
4. Vendor must be the seller/company name.
5. Vendor must NEVER be "Subtotal", "Tax", "Total", "Invoice",
   "Date", "Due Date", or any monetary value.
6. Invoice number must be the actual identifier such as
   INV-2026-0510.
7. Do not return "Invoice" as the invoice number.
8. Invoice date must come from the Date field.
9. Due date must come from the Due Date field.
10. Subtotal must come from the Subtotal field.
11. Tax must come from Tax, Sales Tax, VAT or GST.
12. Total must come from Total Due, Total Amount, Amount Due,
    Balance Due or Grand Total.
13. Do not calculate a value when the actual value exists in text.
14. Preserve the exact meaning of line items.
15. Return ONLY valid JSON.
16. Do not include markdown.
17. Do not add comments inside JSON.

Required JSON:

{{
    "vendor": "",
    "customer_name": "",
    "invoice_number": "",
    "invoice_date": "",
    "due_date": "",
    "subtotal": 0.00,
    "tax": 0.00,
    "total": 0.00,
    "currency": "",
    "payment_info": "",
    "line_items": [
        {{
            "description": "",
            "quantity": 1,
            "unit_price": 0.00,
            "amount": 0.00
        }}
    ],
    "validation_flags": [],
    "confidence": 0,
    "reasoning": ""
}}

Document Filename:
{filename}

INVOICE TEXT:
{raw_text[:12000]}
"""

        response_text = self.call_gemini(
            prompt,
            system_instruction=(
                "You are a high-accuracy invoice OCR and "
                "financial document extraction engine. "
                "Extract only values supported by the document."
            )
        )

        extracted = self._clean_json_response(
            response_text
        )

        # ---------------------------------------------------------------------
        # Gemini extraction succeeded
        # ---------------------------------------------------------------------

        if extracted:

            # Make sure required containers exist
            extracted.setdefault(
                "line_items",
                []
            )

            extracted.setdefault(
                "validation_flags",
                []
            )

            # Validate against original invoice text
            extracted = self._validate_invoice_data(
                extracted,
                raw_text
            )

            return extracted

        # ---------------------------------------------------------------------
        # Gemini failed -> deterministic fallback
        # ---------------------------------------------------------------------

        return self._heuristic_invoice_extraction(
            raw_text,
            filename
        )

    # =========================================================================
    # INVOICE HEURISTIC FALLBACK
    # =========================================================================

    def _heuristic_invoice_extraction(
        self,
        text: str,
        filename: str
    ) -> dict:

        """
        Rule-based invoice extraction fallback.

        This version avoids fake values and avoids assigning
        monetary fields to vendor/customer fields.
        """

        vendor = self._extract_vendor(text)

        customer = self._extract_customer(text)

        invoice_number = self._extract_invoice_number(
            text
        )

        invoice_date, due_date = self._extract_invoice_dates(
            text
        )

        subtotal = self._extract_money_after_label(
            text,
            [
                r"subtotal",
                r"sub\s*total",
                r"net\s+amount"
            ]
        )

        tax = self._extract_money_after_label(
            text,
            [
                r"sales\s+tax",
                r"tax",
                r"gst",
                r"vat"
            ]
        )

        total = self._extract_money_after_label(
            text,
            [
                r"total\s+amount\s+due",
                r"total\s+due",
                r"total\s+amount",
                r"amount\s+due",
                r"balance\s+due",
                r"grand\s+total",
                r"total"
            ]
        )

        if subtotal is None:
            subtotal = 0.0

        if tax is None:
            tax = 0.0

        if total is None:
            total = 0.0

        # ---------------------------------------------------------------------
        # Payment information
        # ---------------------------------------------------------------------

        payment_info = "Not specified"

        payment_patterns = [

            r"(?im)^\s*payment\s+via\s*[:\-]?\s*(.+?)\s*$",

            r"(?im)^\s*payment\s+method\s*[:\-]?\s*(.+?)\s*$",

            r"(?im)^\s*payment\s+terms?\s*[:\-]?\s*(.+?)\s*$",
        ]

        for pattern in payment_patterns:

            match = re.search(
                pattern,
                text
            )

            if match:

                payment_info = match.group(1).strip()
                break

        # ---------------------------------------------------------------------
        # Validation
        # ---------------------------------------------------------------------

        validation_flags = []

        if not vendor:
            validation_flags.append(
                "Vendor name not found"
            )

        if not invoice_number:
            validation_flags.append(
                "Invoice number not found"
            )

        if not invoice_date:
            validation_flags.append(
                "Invoice date not found"
            )

        if not due_date:
            validation_flags.append(
                "Due date not found"
            )

        if not customer:
            validation_flags.append(
                "Customer / Billed To not found"
            )

        # ---------------------------------------------------------------------
        # Math check
        # ---------------------------------------------------------------------

        if (
            subtotal > 0
            and total > 0
        ):

            expected = round(
                subtotal + tax,
                2
            )

            if abs(expected - total) > 0.05:

                validation_flags.append(
                    f"Math discrepancy: "
                    f"Subtotal ({subtotal:.2f}) + "
                    f"Tax ({tax:.2f}) != "
                    f"Total ({total:.2f})"
                )

        # ---------------------------------------------------------------------
        # Confidence
        # ---------------------------------------------------------------------

        confidence = 95

        confidence -= min(
            len(validation_flags) * 8,
            40
        )

        confidence = max(
            20,
            min(confidence, 99)
        )

        # ---------------------------------------------------------------------
        # Line item
        # ---------------------------------------------------------------------

        line_items = []

        if subtotal > 0:

            line_items.append(
                {
                    "description": "Invoice items",
                    "quantity": 1,
                    "unit_price": round(
                        subtotal,
                        2
                    ),
                    "amount": round(
                        subtotal,
                        2
                    )
                }
            )

        return {
            "vendor": vendor or "Not found",

            "customer_name":
                customer or "Not found",

            "invoice_number":
                invoice_number or "Not found",

            "invoice_date":
                invoice_date or "Not found",

            "due_date":
                due_date or "Not found",

            "subtotal":
                round(subtotal, 2),

            "tax":
                round(tax, 2),

            "total":
                round(total, 2),

            "currency":
                self._detect_currency(text),

            "payment_info":
                payment_info,

            "line_items":
                line_items,

            "validation_flags":
                validation_flags
                if validation_flags
                else ["All validation checks passed"],

            "confidence":
                confidence,

            "reasoning":
                "Invoice extracted using rule-based "
                "field detection and mathematical validation."
        }

    # =========================================================================
    # 2. LEAD SCORING
    # =========================================================================

    def score_lead(
        self,
        lead_data: dict
    ) -> dict:

        prompt = f"""
You are an AI Sales Intelligence Agent.

Evaluate this sales lead and return ONLY valid JSON.

Lead Information:

Name: {lead_data.get('name')}
Company: {lead_data.get('company')}
Industry: {lead_data.get('industry')}
Company Size: {lead_data.get('company_size')}
Budget: ${lead_data.get('budget', 0)}
Product Interest: {lead_data.get('product')}
Source: {lead_data.get('source')}
Previous Interaction: {lead_data.get('previous_interaction')}
Engagement Level: {lead_data.get('engagement')}

Return:

{{
    "score": 88,
    "category": "HOT",
    "reasons": [],
    "recommended_action": "",
    "recommended_department": "Sales",
    "confidence": 92
}}

Category rules:

HOT = 80-100
WARM = 60-79
COLD = 0-59
"""

        response_text = self.call_gemini(
            prompt,
            system_instruction=(
                "You calculate accurate B2B lead scores "
                "and return valid JSON."
            )
        )

        scored = self._clean_json_response(
            response_text
        )

        if (
            scored
            and "score" in scored
            and "category" in scored
        ):

            try:

                scored["score"] = int(
                    scored.get("score", 70)
                )

                scored["confidence"] = int(
                    scored.get("confidence", 90)
                )

                return scored

            except Exception:
                pass

        return self._heuristic_lead_scoring(
            lead_data
        )

    def _heuristic_lead_scoring(
        self,
        data: dict
    ) -> dict:

        score = 20
        reasons = []

        try:
            budget = float(
                data.get("budget", 0) or 0
            )
        except Exception:
            budget = 0

        size = str(
            data.get("company_size", "")
        ).lower()

        engagement = str(
            data.get("engagement", "medium")
        ).lower()

        interaction = str(
            data.get("previous_interaction", "")
        ).lower()

        source = str(
            data.get("source", "")
        ).lower()

        # Budget
        if budget >= 50000:
            score += 35
            reasons.append(
                f"High enterprise budget (${budget:,.0f})"
            )

        elif budget >= 20000:
            score += 25
            reasons.append(
                f"Strong mid-market budget (${budget:,.0f})"
            )

        elif budget >= 5000:
            score += 15
            reasons.append(
                f"Standard SMB budget (${budget:,.0f})"
            )

        elif budget > 0:
            score += 5
            reasons.append(
                "Modest initial budget"
            )

        else:
            reasons.append(
                "No stated budget"
            )

        # Company size
        if (
            "1000+" in size
            or "enterprise" in size
            or "500+" in size
        ):

            score += 20

            reasons.append(
                "Enterprise scale organization"
            )

        elif (
            "201-1000" in size
            or "51-200" in size
        ):

            score += 15

            reasons.append(
                "High growth mid-sized organization"
            )

        elif "11-50" in size:

            score += 10

            reasons.append(
                "Small business team"
            )

        else:

            score += 5

        # Engagement
        if "high" in engagement:

            score += 20

            reasons.append(
                "High engagement"
            )

        elif "medium" in engagement:

            score += 10

            reasons.append(
                "Moderate engagement"
            )

        else:

            reasons.append(
                "Low engagement"
            )

        # Previous interaction
        if "demo" in interaction:

            score += 15

            reasons.append(
                "Explicit live demo requested"
            )

        elif (
            "webinar" in interaction
            or "whitepaper" in interaction
        ):

            score += 10

            reasons.append(
                "Attended webinar or downloaded whitepaper"
            )

        elif "pricing" in interaction:

            score += 12

            reasons.append(
                "Strong pricing interest"
            )

        # Source
        if (
            "referral" in source
            or "inbound" in source
        ):

            score += 10

            reasons.append(
                "High-intent acquisition channel"
            )

        score = max(
            5,
            min(99, score)
        )

        if score >= 80:

            category = "HOT"

            action = (
                "Immediate direct sales outreach "
                "and custom solution demo"
            )

            department = "Sales"

        elif score >= 60:

            category = "WARM"

            action = (
                "Nurture with case studies "
                "and technical briefing"
            )

            department = "Sales"

        else:

            category = "COLD"

            action = (
                "Enroll in automated "
                "email marketing campaign"
            )

            department = "Marketing"

        return {
            "score": score,
            "category": category,
            "reasons": reasons,
            "recommended_action": action,
            "recommended_department": department,
            "confidence": 92
        }

    # =========================================================================
    # 3. RESUME SCREENING & JD MATCHING
    # =========================================================================

    def screen_resume(
        self,
        resume_text: str,
        job_description: str,
        job_skills: list = None
    ) -> dict:

        skills_str = (
            ", ".join(job_skills)
            if job_skills
            else "General technical skills"
        )

        prompt = f"""
You are an expert HR Assistant AI.

Screen the candidate resume against the Job Description.

Return ONLY valid JSON.

Required structure:

{{
    "candidate_name": "Full Name",
    "email": "",
    "phone": "",
    "skills": [],
    "experience": "",
    "education": "",
    "certifications": [],
    "match_score": 88,
    "skills_match_pct": 90,
    "experience_match_pct": 85,
    "matching_skills": [],
    "missing_skills": [],
    "recommendation": "Strong Match",
    "ai_summary": "",
    "confidence": 92
}}

Target Job Skills:
{skills_str}

Job Description:
{job_description[:5000]}

Candidate Resume:
{resume_text[:10000]}
"""

        response_text = self.call_gemini(
            prompt,
            system_instruction=(
                "You screen resumes objectively "
                "and return valid JSON."
            )
        )

        screened = self._clean_json_response(
            response_text
        )

        if (
            screened
            and "candidate_name" in screened
            and "match_score" in screened
        ):

            try:

                screened["match_score"] = int(
                    screened.get("match_score", 75)
                )

                screened["skills_match_pct"] = int(
                    screened.get(
                        "skills_match_pct",
                        70
                    )
                )

                screened["experience_match_pct"] = int(
                    screened.get(
                        "experience_match_pct",
                        70
                    )
                )

                screened["confidence"] = int(
                    screened.get(
                        "confidence",
                        90
                    )
                )

                return screened

            except Exception:
                pass

        return self._heuristic_resume_screening(
            resume_text,
            job_description,
            job_skills
        )

    def _heuristic_resume_screening(
        self,
        text: str,
        jd: str,
        target_skills: list = None
    ) -> dict:

        lines = [
            line.strip()
            for line in text.split("\n")
            if line.strip()
        ]

        name = "Candidate"

        for line in lines[:5]:

            if (
                len(line.split()) in (2, 3, 4)
                and not any(
                    k in line.lower()
                    for k in [
                        "resume",
                        "curriculum",
                        "page",
                        "email",
                        "phone",
                        "http"
                    ]
                )
            ):

                name = line
                break

        email_match = re.search(
            r"[\w.+-]+@[\w-]+\.[\w.-]+",
            text
        )

        email = (
            email_match.group(0)
            if email_match
            else "Not found"
        )

        phone_match = re.search(
            r"(?:\+?\d{1,3}[-.\s]?)?"
            r"\(?\d{3}\)?[-.\s]?"
            r"\d{3}[-.\s]?"
            r"\d{4}",
            text
        )

        phone = (
            phone_match.group(0)
            if phone_match
            else "Not found"
        )

        tech_dict = [

            "python",
            "javascript",
            "typescript",
            "react",
            "angular",
            "vue",
            "node.js",
            "flask",
            "django",
            "fastapi",
            "sql",
            "postgresql",
            "mysql",
            "sqlite",
            "mongodb",
            "aws",
            "azure",
            "gcp",
            "docker",
            "kubernetes",
            "git",
            "ci/cd",
            "rest api",
            "graphql",
            "machine learning",
            "ai",
            "pandas",
            "html5",
            "css3",
            "bootstrap",
            "tailwind",
            "c++",
            "java",
            "c#",
            "go",
            "ruby",
            "linux",
            "agile",
            "scrum",
            "project management",
            "accounting",
            "financial analysis",
            "excel",
            "salesforce"
        ]

        text_lower = text.lower()

        extracted_skills = []

        for skill in tech_dict:

            pattern = (
                r"(?<!\w)"
                + re.escape(skill)
                + r"(?!\w)"
            )

            if re.search(
                pattern,
                text_lower
            ):

                extracted_skills.append(
                    skill.title()
                )

        if not target_skills:

            target_skills = []

            for skill in tech_dict:

                pattern = (
                    r"(?<!\w)"
                    + re.escape(skill)
                    + r"(?!\w)"
                )

                if re.search(
                    pattern,
                    jd.lower()
                ):

                    target_skills.append(
                        skill.title()
                    )

        if not target_skills:

            target_skills = [
                "Python",
                "Flask",
                "SQL",
                "JavaScript",
                "Docker"
            ]

        matched = [
            s
            for s in target_skills
            if any(
                s.lower() == ext.lower()
                for ext in extracted_skills
            )
        ]

        missing = [
            s
            for s in target_skills
            if not any(
                s.lower() == ext.lower()
                for ext in extracted_skills
            )
        ]

        skills_pct = int(
            round(
                (
                    len(matched)
                    /
                    max(1, len(target_skills))
                )
                * 100
            )
        )

        exp_match = re.search(
            r"(\d+)\+?\s*(?:years|yrs)"
            r"(?:\s+of)?\s+experience",
            text_lower
        )

        exp_years = (
            int(exp_match.group(1))
            if exp_match
            else 0
        )

        exp_summary = (
            f"{exp_years}+ years of "
            f"relevant industry experience"
        )

        jd_exp_match = re.search(
            r"(\d+)\+?\s*(?:years|yrs)",
            jd.lower()
        )

        jd_req_years = (
            int(jd_exp_match.group(1))
            if jd_exp_match
            else 3
        )

        exp_pct = min(
            100,
            int(
                round(
                    (
                        exp_years
                        /
                        max(1, jd_req_years)
                    )
                    * 100
                )
            )
        )

        edu = (
            "Bachelor's Degree in "
            "Computer Science or Related Field"
        )

        if (
            "master" in text_lower
            or "m.s." in text_lower
            or "mba" in text_lower
        ):

            edu = (
                "Master's Degree / Post-Graduate"
            )

        elif (
            "phd" in text_lower
            or "doctorate" in text_lower
        ):

            edu = (
                "Ph.D. in Technical Discipline"
            )

        elif (
            "bachelor" in text_lower
            or "b.s." in text_lower
            or "b.tech" in text_lower
            or "b.e." in text_lower
        ):

            edu = (
                "Bachelor of Science / B.Tech"
            )

        overall_score = int(
            round(
                (skills_pct * 0.6)
                +
                (exp_pct * 0.4)
            )
        )

        overall_score = max(
            25,
            min(98, overall_score)
        )

        if overall_score >= 80:

            recommendation = "Strong Match"

        elif overall_score >= 60:

            recommendation = "Review"

        else:

            recommendation = "Low Match"

        summary = (
            f"Candidate matches "
            f"{len(matched)} of "
            f"{len(target_skills)} "
            f"required key skills "
            f"({skills_pct}%) with approximately "
            f"{exp_years} years demonstrated experience."
        )

        return {

            "candidate_name": name,

            "email": email,

            "phone": phone,

            "skills":
                extracted_skills
                if extracted_skills
                else ["No skills found"],

            "experience": exp_summary,

            "education": edu,

            "certifications": [],

            "match_score": overall_score,

            "skills_match_pct": skills_pct,

            "experience_match_pct": exp_pct,

            "matching_skills": matched,

            "missing_skills": missing,

            "recommendation": recommendation,

            "ai_summary": summary,

            "confidence": 90
        }

    # =========================================================================
    # 4. SUPPORT TICKET CLASSIFICATION
    # =========================================================================

    def classify_ticket(
        self,
        subject: str,
        description: str
    ) -> dict:

        prompt = f"""
You are an AI Support Automation Engine.

Classify this customer support ticket.

Return ONLY valid JSON:

{{
    "category": "Billing",
    "priority": "High",
    "sentiment": "Negative",
    "department": "Finance",
    "reasoning": "",
    "confidence": 94
}}

Subject:
{subject}

Description:
{description}
"""

        response_text = self.call_gemini(
            prompt,
            system_instruction=(
                "You classify support tickets accurately "
                "and return JSON."
            )
        )

        classified = self._clean_json_response(
            response_text
        )

        if (
            classified
            and "category" in classified
            and "priority" in classified
            and "sentiment" in classified
        ):

            try:

                classified["confidence"] = int(
                    classified.get(
                        "confidence",
                        88
                    )
                )

                return classified

            except Exception:
                pass

        return self._heuristic_ticket_classification(
            subject,
            description
        )

    def _heuristic_ticket_classification(
        self,
        subject: str,
        desc: str
    ) -> dict:

        text = (
            f"{subject} {desc}"
        ).lower()

        # Category
        if any(
            w in text
            for w in [
                "payment",
                "deducted",
                "charged",
                "invoice",
                "refund",
                "billing",
                "subscription",
                "price",
                "credit card",
                "receipt"
            ]
        ):

            category = "Billing"
            department = "Finance"

        elif any(
            w in text
            for w in [
                "bug",
                "error",
                "crash",
                "broken",
                "not working",
                "api",
                "server",
                "500",
                "404",
                "slow",
                "timeout",
                "code"
            ]
        ):

            category = "Technical"
            department = "Support"

        elif any(
            w in text
            for w in [
                "password",
                "login",
                "2fa",
                "sso",
                "access",
                "permission",
                "profile",
                "locked out",
                "reset"
            ]
        ):

            category = "Account"
            department = "Support"

        elif any(
            w in text
            for w in [
                "feature",
                "upgrade",
                "enterprise",
                "demo",
                "purchase",
                "sales",
                "quote",
                "contract"
            ]
        ):

            category = "Product"
            department = "Sales"

        else:

            category = "General"
            department = "Support"

        # Sentiment
        if any(
            w in text
            for w in [
                "furious",
                "horrible",
                "worst",
                "unacceptable",
                "deducted twice",
                "scam",
                "angry",
                "terrible",
                "fail",
                "broken",
                "urgent",
                "immediately"
            ]
        ):

            sentiment = "Negative"

        elif any(
            w in text
            for w in [
                "thank",
                "great",
                "love",
                "helpful",
                "awesome",
                "appreciate",
                "kudos"
            ]
        ):

            sentiment = "Positive"

        else:

            sentiment = "Neutral"

        # Priority
        if any(
            w in text
            for w in [
                "emergency",
                "critical",
                "production down",
                "security breach",
                "data loss",
                "all users blocked"
            ]
        ):

            priority = "Critical"

        elif (
            sentiment == "Negative"
            or any(
                w in text
                for w in [
                    "twice",
                    "deducted",
                    "charged",
                    "blocked",
                    "urgent",
                    "cannot access",
                    "high"
                ]
            )
        ):

            priority = "High"

        elif category in (
            "Technical",
            "Account"
        ):

            priority = "Medium"

        else:

            priority = "Low"

        confidence = 90

        if (
            priority == "Critical"
            or sentiment == "Negative"
        ):

            confidence = 85

        return {

            "category": category,

            "priority": priority,

            "sentiment": sentiment,

            "department": department,

            "reasoning":
                f"Identified category '{category}' "
                f"and '{sentiment}' sentiment "
                f"based on keyword analysis.",

            "confidence": confidence
        }

    # =========================================================================
    # SUPPORT RESPONSE GENERATION
    # =========================================================================

    def generate_support_response(
        self,
        customer_name: str,
        subject: str,
        description: str,
        category: str,
        sentiment: str
    ) -> str:

        prompt = f"""
You are a courteous and professional customer support
specialist for SmartBiz.

Write a warm, empathetic and clear response.

Customer Name:
{customer_name}

Subject:
{subject}

Customer Complaint:
{description}

Category:
{category}

Sentiment:
{sentiment}

Requirements:

1. Address the customer by name.
2. Apologize when appropriate.
3. Explain the next action clearly.
4. Keep the response professional.
5. End with:

SmartBiz Customer Care Team
"""

        response_text = self.call_gemini(
            prompt,
            system_instruction=(
                "You write polished customer support responses."
            )
        )

        if (
            response_text
            and len(response_text.strip()) > 30
        ):

            return response_text.strip()

        # ---------------------------------------------------------------------
        # Fallback
        # ---------------------------------------------------------------------

        first_name = (
            customer_name.split()[0]
            if customer_name
            else "Valued Customer"
        )

        if category == "Billing":

            return (
                f"Dear {first_name},\n\n"
                f"Thank you for contacting SmartBiz Support "
                f"regarding \"{subject}\".\n\n"
                f"We apologize for the inconvenience. "
                f"Our Finance Department has been notified "
                f"and will review the billing transaction "
                f"and correct any duplicate or incorrect charge.\n\n"
                f"You will receive an update once the review "
                f"is completed.\n\n"
                f"Best regards,\n"
                f"SmartBiz Customer Care Team"
            )

        elif category == "Technical":

            return (
                f"Dear {first_name},\n\n"
                f"Thank you for reporting \"{subject}\".\n\n"
                f"Our technical support team has been notified "
                f"and is investigating the issue.\n\n"
                f"We will work to resolve the problem as quickly "
                f"as possible and keep you updated.\n\n"
                f"Best regards,\n"
                f"SmartBiz Technical Support Team"
            )

        elif category == "Account":

            return (
                f"Dear {first_name},\n\n"
                f"Thank you for contacting SmartBiz regarding "
                f"your account and \"{subject}\".\n\n"
                f"Our support team will help you securely "
                f"restore access to your account.\n\n"
                f"Best regards,\n"
                f"SmartBiz Account Security Team"
            )

        else:

            return (
                f"Dear {first_name},\n\n"
                f"Thank you for contacting SmartBiz Support "
                f"regarding \"{subject}\".\n\n"
                f"We have received your request and routed it "
                f"to the appropriate team for review.\n\n"
                f"Best regards,\n"
                f"SmartBiz Customer Care Team"
            )


# ============================================================================
# GLOBAL SINGLETON AI SERVICE INSTANCE
# ============================================================================

ai_service = AIService()