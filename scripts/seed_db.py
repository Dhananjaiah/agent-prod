"""Database seeding script with realistic synthetic data."""
import random
import uuid
from datetime import datetime, timedelta
from decimal import Decimal

from faker import Faker
from sqlalchemy.orm import Session

from app.config.logging import get_logger, setup_logging
from app.db.models import Base, Claim, Customer, Document, Policy
from app.db.session import SyncSessionLocal, sync_engine

setup_logging()
logger = get_logger(__name__)
fake = Faker()
Faker.seed(42)
random.seed(42)


# Configuration
NUM_CUSTOMERS = 300
NUM_POLICIES = 500
NUM_CLAIMS = 1200
NUM_DOCUMENTS = 1500


# Enums
POLICY_TYPES = ["auto", "home", "life", "health", "travel"]
POLICY_STATUSES = ["active", "expired", "cancelled", "pending"]
CLAIM_TYPES = ["accident", "theft", "damage", "medical", "liability", "natural_disaster"]
CLAIM_STATUSES = ["submitted", "under_review", "approved", "denied", "paid", "closed"]
DOCUMENT_TYPES = [
    "policy_document",
    "claim_form",
    "evidence",
    "invoice",
    "correspondence",
    "id_proof",
    "medical_report",
]
STORAGE_PROVIDERS = ["s3", "sharepoint", "local"]
MIME_TYPES = [
    "application/pdf",
    "image/jpeg",
    "image/png",
    "application/msword",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
]


def create_customers(session: Session) -> list[Customer]:
    """Create synthetic customer data."""
    logger.info(f"Creating {NUM_CUSTOMERS} customers...")
    customers = []

    for _ in range(NUM_CUSTOMERS):
        customer = Customer(
            id=uuid.uuid4(),
            email=fake.unique.email(),
            first_name=fake.first_name(),
            last_name=fake.last_name(),
            phone=fake.phone_number()[:20],
            address=fake.street_address(),
            city=fake.city(),
            state=fake.state_abbr(),
            zip_code=fake.zipcode(),
            date_of_birth=fake.date_of_birth(minimum_age=18, maximum_age=85),
        )
        customers.append(customer)
        session.add(customer)

    session.commit()
    logger.info(f"Created {len(customers)} customers")
    return customers


def create_policies(session: Session, customers: list[Customer]) -> list[Policy]:
    """Create synthetic policy data."""
    logger.info(f"Creating {NUM_POLICIES} policies...")
    policies = []

    for i in range(NUM_POLICIES):
        customer = random.choice(customers)
        policy_type = random.choice(POLICY_TYPES)
        status = random.choices(
            POLICY_STATUSES, weights=[0.7, 0.15, 0.1, 0.05], k=1
        )[0]

        start_date = fake.date_between(start_date="-3y", end_date="today")
        end_date = start_date + timedelta(days=365)

        # Set premium and coverage based on policy type
        premium_multiplier = {
            "auto": (500, 2000),
            "home": (800, 3000),
            "life": (200, 1000),
            "health": (300, 1500),
            "travel": (50, 300),
        }
        coverage_multiplier = {
            "auto": (10000, 100000),
            "home": (100000, 1000000),
            "life": (50000, 500000),
            "health": (50000, 250000),
            "travel": (5000, 50000),
        }

        premium_range = premium_multiplier.get(policy_type, (500, 2000))
        coverage_range = coverage_multiplier.get(policy_type, (50000, 200000))

        policy = Policy(
            id=uuid.uuid4(),
            policy_number=f"POL-{policy_type.upper()}-{i+10001:05d}",
            customer_id=customer.id,
            policy_type=policy_type,
            status=status,
            premium_amount=Decimal(str(round(random.uniform(*premium_range), 2))),
            coverage_amount=Decimal(str(round(random.uniform(*coverage_range), 2))),
            deductible=Decimal(str(round(random.uniform(250, 2500), 2))),
            start_date=datetime.combine(start_date, datetime.min.time()),
            end_date=datetime.combine(end_date, datetime.min.time()),
            description=fake.paragraph(nb_sentences=2),
        )
        policies.append(policy)
        session.add(policy)

    session.commit()
    logger.info(f"Created {len(policies)} policies")
    return policies


def create_claims(session: Session, policies: list[Policy]) -> list[Claim]:
    """Create synthetic claim data."""
    logger.info(f"Creating {NUM_CLAIMS} claims...")
    claims = []

    # Only create claims for active policies
    active_policies = [p for p in policies if p.status == "active"]

    for i in range(NUM_CLAIMS):
        policy = random.choice(active_policies)
        claim_type = random.choice(CLAIM_TYPES)
        status = random.choice(CLAIM_STATUSES)

        incident_date = fake.date_between(
            start_date=policy.start_date.date(),
            end_date=min(policy.end_date.date(), datetime.now().date()),
        )
        filed_date = incident_date + timedelta(days=random.randint(0, 30))

        claim_amount = round(
            random.uniform(100, float(policy.coverage_amount) * 0.3), 2
        )
        approved_amount = None
        resolution_notes = None

        if status in ["approved", "paid", "closed"]:
            approved_amount = Decimal(
                str(round(claim_amount * random.uniform(0.5, 1.0), 2))
            )
            resolution_notes = fake.paragraph(nb_sentences=1)
        elif status == "denied":
            resolution_notes = random.choice([
                "Claim denied due to policy exclusion.",
                "Insufficient documentation provided.",
                "Incident occurred outside coverage period.",
                "Deductible not met.",
                "Pre-existing condition exclusion applies.",
            ])

        claim = Claim(
            id=uuid.uuid4(),
            claim_number=f"CLM-2024-{i+1:05d}",
            policy_id=policy.id,
            status=status,
            claim_type=claim_type,
            claim_amount=Decimal(str(claim_amount)),
            approved_amount=approved_amount,
            incident_date=datetime.combine(incident_date, datetime.min.time()),
            filed_date=datetime.combine(filed_date, datetime.min.time()),
            description=fake.paragraph(nb_sentences=3),
            resolution_notes=resolution_notes,
        )
        claims.append(claim)
        session.add(claim)

    session.commit()
    logger.info(f"Created {len(claims)} claims")
    return claims


def create_documents(
    session: Session, policies: list[Policy], claims: list[Claim]
) -> list[Document]:
    """Create synthetic document data."""
    logger.info(f"Creating {NUM_DOCUMENTS} documents...")
    documents = []

    for i in range(NUM_DOCUMENTS):
        doc_type = random.choice(DOCUMENT_TYPES)
        storage_provider = random.choice(STORAGE_PROVIDERS)
        mime_type = random.choice(MIME_TYPES)

        # Determine file extension based on MIME type
        ext_map = {
            "application/pdf": "pdf",
            "image/jpeg": "jpg",
            "image/png": "png",
            "application/msword": "doc",
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document": "docx",
        }
        extension = ext_map.get(mime_type, "pdf")

        # Associate with policy, claim, or both
        policy_id = None
        claim_id = None

        if random.random() < 0.4:
            # Document for a claim
            claim = random.choice(claims)
            claim_id = claim.id
            policy_id = claim.policy_id
        else:
            # Document for a policy
            policy = random.choice(policies)
            policy_id = policy.id

        document = Document(
            id=uuid.uuid4(),
            document_name=f"{doc_type.replace('_', ' ').title()}_{i+1:05d}.{extension}",
            document_type=doc_type,
            storage_path=f"{storage_provider}://insurance-docs/{doc_type}/{uuid.uuid4()}.{extension}",
            storage_provider=storage_provider,
            file_size_bytes=random.randint(10000, 10000000),
            mime_type=mime_type,
            policy_id=policy_id,
            claim_id=claim_id,
            uploaded_by=fake.email(),
            is_archived=random.random() < 0.1,
        )
        documents.append(document)
        session.add(document)

    session.commit()
    logger.info(f"Created {len(documents)} documents")
    return documents


def seed_database() -> None:
    """Seed the database with synthetic data."""
    logger.info("Starting database seeding...")

    # Create all tables
    Base.metadata.create_all(bind=sync_engine)
    logger.info("Database tables created")

    with SyncSessionLocal() as session:
        # Check if data already exists
        existing_customers = session.query(Customer).count()
        if existing_customers > 0:
            logger.info(
                f"Database already contains {existing_customers} customers. Skipping seeding."
            )
            return

        # Create data
        customers = create_customers(session)
        policies = create_policies(session, customers)
        claims = create_claims(session, policies)
        documents = create_documents(session, policies, claims)

        logger.info(
            "Database seeding complete",
            customers=len(customers),
            policies=len(policies),
            claims=len(claims),
            documents=len(documents),
        )


if __name__ == "__main__":
    seed_database()
