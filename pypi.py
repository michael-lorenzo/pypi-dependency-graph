import re

import networkx as nx
import requests
import tqdm
from packaging.requirements import Requirement
from sqlalchemy import Column, Integer, PickleType, Text, create_engine, delete, select
from sqlalchemy.orm import Session, declarative_base

Base = declarative_base()
req = requests.Session()


class Package(Base):
    __tablename__ = "packages"

    name = Column(Text, primary_key=True)
    last_serial = Column(Integer)
    info = Column(PickleType)
    requirements = Column(Text)

    def __repr__(self) -> str:
        return f"<Package(name={self.name})>"


def normalize_name(name):  # PEP 503
    return re.sub(r"[-_.]+", "-", name).lower()


def list_packages_with_serial():  # PEP 691
    projects = requests.get("https://pypi.org/simple/", headers={"Accept": "application/vnd.pypi.simple.v1+json"}).json()["projects"]
    return {normalize_name(p["name"]): p["_last-serial"] for p in projects}


def get_metadata(project):
    data = req.get(f"https://pypi.org/pypi/{project}/json")
    if data.ok:
        return data.json()
    return None


def get_requirements(data):
    pkgs = set()
    if data["info"]["requires_dist"]:
        for req in data["info"]["requires_dist"]:
            try:
                r = Requirement(req)
                if r.marker is None or r.marker.evaluate({"extra": "", "sys_platform": "linux"}):
                    pkgs.add(normalize_name(r.name))
            except Exception:
                pass
    return " ".join(sorted(pkgs))


if __name__ == "__main__":
    engine = create_engine("sqlite:///pypi.db", future=True)
    Base.metadata.create_all(engine)

    with Session(engine) as session:
        print("Query API")
        packages = list_packages_with_serial()
        packages_db = dict(session.execute(select(Package.name, Package.last_serial)).all())
        creatable = list(packages.keys() - packages_db.keys())
        updatable = [p for p in packages if p in packages_db and packages[p] > packages_db[p]]
        updatable = session.scalars(select(Package).where(Package.name.in_(updatable))).all()
        deletable = list(packages_db.keys() - packages.keys())
        # Create
        print(f"Creating {len(creatable)} packages")
        for name in tqdm.tqdm(creatable):
            data = get_metadata(name)
            if data:
                p = Package(name=name, last_serial=data["last_serial"], info=data["info"], requirements=get_requirements(data))
            else:
                p = Package(name=name, last_serial=packages[name])
            session.add(p)
            session.commit()
        # Update
        print(f"Updating {len(updatable)} packages")
        for pkg in tqdm.tqdm(updatable):
            data = get_metadata(pkg.name)
            if data:
                pkg.last_serial = data["last_serial"]
                pkg.info = data["info"]
                requirements = get_requirements(data)
                session.commit()
        # Delete
        print(f"Deleting {len(deletable)} packages")
        session.execute(delete(Package).where(Package.name.in_(deletable)))
        session.commit()
        # Save Graph
        print(f"Save Graph")
        adjlist = session.execute(select(Package.name, Package.requirements).where(Package.requirements != None)).all()
        adjlist = [f"{a} {b}".strip() for a, b in adjlist]
        G = nx.parse_adjlist(adjlist, create_using=nx.DiGraph)
        nx.write_gexf(G, "pypi.gexf")
