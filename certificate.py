import streamlit as st
import requests
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from datetime import date
import uuid
import qrcode

# =====================================================
# PAGE SETUP
# =====================================================

st.set_page_config(
    page_title="Smart Campus Certificates",
    page_icon="🎓",
    layout="wide"
)

CERTIFICATE_THRESHOLD = 60

APP_URL = "https://smart-campus-certificate-9wv5la9yqmbnpso5zzjbsr.streamlit.app"

# =====================================================
# SUPABASE CONFIG
# =====================================================

SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]

TABLE_URL = f"{SUPABASE_URL}/rest/v1/certificates"

HEADERS = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json"
}


# =====================================================
# SUPABASE FUNCTIONS
# =====================================================

def add_student(
    student_name,
    course_name,
    completion,
    assessment
):

    certificate_id = generate_certificate_id()
    issue_date = date.today().strftime("%d %B %Y")

    data = {
        "certificate_id": certificate_id,
        "student_name": student_name,
        "course_name": course_name,
        "completion": int(completion),
        "assessment": assessment,
        "issue_date": issue_date
    }

    response = requests.post(
        TABLE_URL,
        headers=HEADERS,
        json=data
    )

    return response


def get_students():

    response = requests.get(
        TABLE_URL,
        headers=HEADERS,
        params={
            "select": "*",
            "order": "id.desc"
        }
    )

    if response.status_code == 200:
        return response.json()

    return []


def get_student_by_certificate(certificate_id):

    response = requests.get(
        TABLE_URL,
        headers=HEADERS,
        params={
            "certificate_id": f"eq.{certificate_id}",
            "select": "*"
        }
    )

    if response.status_code == 200:

        data = response.json()

        if data:
            return data[0]

    return None


def generate_certificate_id():

    return (
        "SC-"
        + str(uuid.uuid4())[:8].upper()
    )


def update_certificate(
    student_id,
    certificate_id,
    issue_date
):

    response = requests.patch(
        TABLE_URL,
        headers=HEADERS,
        params={
            "id": f"eq.{student_id}"
        },
        json={
            "certificate_id": certificate_id,
            "issue_date": issue_date
        }
    )

    return response


# =====================================================
# QR CODE
# =====================================================

def create_qr(certificate_id):

    verification_url = (
        f"{APP_URL}/?verify={certificate_id}"
    )

    qr = qrcode.QRCode(
        version=1,
        box_size=8,
        border=4
    )

    qr.add_data(verification_url)
    qr.make(fit=True)

    qr_image = qr.make_image()

    qr_file = f"qr_{certificate_id}.png"

    qr_image.save(qr_file)

    return qr_file


# =====================================================
# PDF CERTIFICATE
# =====================================================

def create_certificate(
    student_name,
    course_name,
    completion,
    certificate_id,
    issue_date
):

    pdf_file = (
        f"certificate_{certificate_id}.pdf"
    )

    qr_file = create_qr(
        certificate_id
    )

    pdf = canvas.Canvas(
        pdf_file,
        pagesize=A4
    )

    width, height = A4

    # Border
    pdf.rect(
        40,
        40,
        width - 80,
        height - 80
    )

    # Title
    pdf.setFont(
        "Helvetica-Bold",
        28
    )

    pdf.drawCentredString(
        width / 2,
        height - 120,
        "CERTIFICATE OF COMPLETION"
    )

    # Organization
    pdf.setFont(
        "Helvetica",
        15
    )

    pdf.drawCentredString(
        width / 2,
        height - 160,
        "SMART CAMPUS"
    )

    # Award text
    pdf.setFont(
        "Helvetica",
        16
    )

    pdf.drawCentredString(
        width / 2,
        height - 230,
        "This certificate is proudly awarded to"
    )

    # Student name
    pdf.setFont(
        "Helvetica-Bold",
        25
    )

    pdf.drawCentredString(
        width / 2,
        height - 275,
        student_name
    )

    # Course
    pdf.setFont(
        "Helvetica",
        16
    )

    pdf.drawCentredString(
        width / 2,
        height - 330,
        "for successfully completing"
    )

    pdf.setFont(
        "Helvetica-Bold",
        20
    )

    pdf.drawCentredString(
        width / 2,
        height - 365,
        course_name
    )

    # Completion
    pdf.setFont(
        "Helvetica",
        14
    )

    pdf.drawCentredString(
        width / 2,
        height - 415,
        f"Course Completion: {completion}%"
    )

    # Date
    pdf.drawString(
        80,
        100,
        f"Issued: {issue_date}"
    )

    # Certificate ID
    pdf.drawString(
        80,
        75,
        f"Certificate ID: {certificate_id}"
    )

    # QR
    pdf.drawImage(
        qr_file,
        width - 170,
        65,
        width=90,
        height=90
    )

    pdf.setFont(
        "Helvetica",
        9
    )

    pdf.drawCentredString(
        width - 125,
        55,
        "SCAN TO VERIFY"
    )

    pdf.save()

    return pdf_file, qr_file


# =====================================================
# QR VERIFICATION MODE
# =====================================================

qr_certificate_id = st.query_params.get(
    "verify",
    ""
)

# =====================================================
# DIRECT QR VERIFICATION PAGE
# =====================================================

if qr_certificate_id:

    certificate_id = (
        qr_certificate_id
        .strip()
        .upper()
    )

    st.title("🔎 Certificate Verification")

    st.write(
        "Smart Campus Certificate Verification"
    )

    st.divider()

    student = get_student_by_certificate(
        certificate_id
    )

    if student:

        st.success(
            "✅ CERTIFICATE VERIFIED"
        )

        st.markdown(
            "### This certificate is valid."
        )

        col1, col2 = st.columns(2)

        with col1:

            st.write("**Student Name**")
            st.write(student["student_name"])

            st.write("**Course**")
            st.write(student["course_name"])

            st.write("**Completion**")
            st.write(
                f'{student["completion"]}%'
            )

        with col2:

            st.write("**Certificate ID**")
            st.code(
                student["certificate_id"]
            )

            st.write("**Issue Date**")
            st.write(
                student["issue_date"]
            )

            st.write("**Assessment**")
            st.write(
                student["assessment"]
            )

        st.divider()

        st.success(
            "🟢 Status: VALID"
        )

        st.caption(
            "Verified using the Smart Campus "
            "online certificate database."
        )

    else:

        st.error(
            "❌ CERTIFICATE NOT FOUND"
        )

        st.write(
            "This certificate ID does not exist "
            "in the Smart Campus database."
        )

    st.stop()


# =====================================================
# NORMAL APPLICATION
# =====================================================

st.sidebar.title(
    "🎓 Smart Campus"
)

view = st.sidebar.radio(
    "Select Panel",
    [
        "🔐 Teacher / Admin",
        "👨‍🎓 Student Certificates",
        "🔎 Verify Certificate"
    ]
)


# =====================================================
# TEACHER / ADMIN
# =====================================================

if view == "🔐 Teacher / Admin":

    st.title(
        "🔐 Teacher / Admin"
    )

    st.write(
        "Record verified student course progress."
    )

    st.subheader(
        "Add Student Academic Record"
    )

    student_name = st.text_input(
        "Student Name"
    )

    course_name = st.text_input(
        "Course Name"
    )

    col1, col2 = st.columns(2)

    with col1:

        modules_completed = st.number_input(
            "Modules Completed",
            min_value=0,
            value=0,
            step=1
        )

    with col2:

        total_modules = st.number_input(
            "Total Modules",
            min_value=1,
            value=1,
            step=1
        )

    assessment = st.selectbox(
        "Final Assessment",
        [
            "Passed",
            "Not Passed"
        ]
    )

    completion = int(
        (modules_completed / total_modules) * 100
    )

    st.info(
        f"📊 Automatic Completion: "
        f"**{completion}%**"
    )

    st.caption(
        f"Certificate eligibility: "
        f"{CERTIFICATE_THRESHOLD}%+ completion "
        f"AND Final Assessment Passed."
    )

    if st.button(
        "💾 Save Student Record",
        use_container_width=True
    ):

        if not student_name.strip():

            st.warning(
                "Please enter student name."
            )

        elif not course_name.strip():

            st.warning(
                "Please enter course name."
            )

        elif modules_completed > total_modules:

            st.error(
                "Completed modules cannot be "
                "greater than total modules."
            )

        else:

            response = add_student(
                student_name,
                course_name,
                completion,
                assessment
            )

            if response.status_code in [200, 201]:

                st.success(
                    "✅ Student record saved "
                    "to online database."
                )

                st.rerun()

            else:

                st.error(
                    "Database error."
                )

                st.code(
                    response.text
                )


# =====================================================
# STUDENT CERTIFICATES
# =====================================================

elif view == "👨‍🎓 Student Certificates":

    st.title(
        "👨‍🎓 Student Certificates"
    )

    st.write(
        "View and generate issued certificates."
    )

    students = get_students()

    if not students:

        st.info(
            "No student records available."
        )

    else:

        for student in students:

            student_id = student["id"]

            name = student["student_name"]

            course = student["course_name"]

            completion = student["completion"]

            assessment = student["assessment"]

            certificate_id = student["certificate_id"]

            issue_date = student["issue_date"]

            with st.expander(
                f"{name} — {course}"
            ):

                st.write(
                    f"**Completion:** "
                    f"{completion}%"
                )

                st.write(
                    f"**Assessment:** "
                    f"{assessment}"
                )

                eligible = (
                    completion >= CERTIFICATE_THRESHOLD
                    and assessment == "Passed"
                )

                if eligible:

                    st.success(
                        "✅ Eligible for certificate."
                    )

                    if not certificate_id:

                        if st.button(
                            "🎓 Generate Certificate ID",
                            key=f"generate_{student_id}"
                        ):

                            new_id = (
                                generate_certificate_id()
                            )

                            today = date.today().strftime(
                                "%d %B %Y"
                            )

                            response = update_certificate(
                                student_id,
                                new_id,
                                today
                            )

                            if response.status_code in [200, 204]:

                                st.success(
                                    "🎉 Certificate generated!"
                                )

                                st.rerun()

                            else:

                                st.error(
                                    "Could not generate certificate."
                                )

                                st.code(
                                    response.text
                                )

                    else:

                        st.write(
                            f"**Certificate ID:** "
                            f"`{certificate_id}`"
                        )

                        if st.button(
                            "📄 Generate Certificate PDF",
                            key=f"pdf_{student_id}"
                        ):

                            pdf_file, qr_file = (
                                create_certificate(
                                    name,
                                    course,
                                    completion,
                                    certificate_id,
                                    issue_date
                                )
                            )

                            st.success(
                                "🎉 Certificate PDF created!"
                            )

                            with open(
                                pdf_file,
                                "rb"
                            ) as file:

                                st.download_button(
                                    "⬇️ Download Certificate",
                                    data=file,
                                    file_name=pdf_file,
                                    mime="application/pdf",
                                    key=f"download_{student_id}"
                                )

                            st.image(
                                qr_file,
                                width=150
                            )

                            st.caption(
                                "Scan this QR code to verify."
                            )

                else:

                    if completion < CERTIFICATE_THRESHOLD:

                        st.warning(
                            f"⚠️ Minimum "
                            f"{CERTIFICATE_THRESHOLD}% "
                            "completion required."
                        )

                    elif assessment != "Passed":

                        st.warning(
                            "⚠️ Final Assessment must be Passed."
                        )


# =====================================================
# MANUAL VERIFICATION
# =====================================================

elif view == "🔎 Verify Certificate":

    st.title(
        "🔎 Certificate Verification"
    )

    certificate_id = st.text_input(
        "Certificate ID",
        placeholder="Example: SC-A12B34CD"
    )

    if st.button(
        "🔍 Verify Certificate",
        use_container_width=True
    ):

        if not certificate_id.strip():

            st.warning(
                "Please enter a certificate ID."
            )

        else:

            certificate_id = (
                certificate_id
                .strip()
                .upper()
            )

            student = get_student_by_certificate(
                certificate_id
            )

            if student:

                st.success(
                    "✅ CERTIFICATE VERIFIED"
                )

                st.write(
                    f'**Student:** '
                    f'{student["student_name"]}'
                )

                st.write(
                    f'**Course:** '
                    f'{student["course_name"]}'
                )

                st.write(
                    f'**Completion:** '
                    f'{student["completion"]}%'
                )

                st.write(
                    f'**Certificate ID:** '
                    f'`{student["certificate_id"]}`'
                )

                st.write(
                    f'**Issued:** '
                    f'{student["issue_date"]}'
                )

                st.success(
                    "🟢 Status: VALID"
                )

            else:

                st.error(
                    "❌ CERTIFICATE NOT FOUND"
                )