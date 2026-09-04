import React, { useEffect, useState } from "react";
import { Link, NavLink, useNavigate } from "react-router-dom";
import { session, signOut } from "../services/auth";

export default function Navbar() {
  const [user, setUser] = useState(session());
  const [open, setOpen] = useState(false);
  const navigate = useNavigate();
  useEffect(() => { const update = () => setUser(session()); window.addEventListener("authchange", update); return () => window.removeEventListener("authchange", update); }, []);
  const close = () => setOpen(false);
  return <nav className="site-nav"><Link className="brand" to="/" onClick={close}>Lens<span>Link</span></Link><button className="nav-toggle" onClick={() => setOpen(!open)} aria-label="Toggle navigation" aria-expanded={open}>☰</button>
    <div className={`nav-links ${open ? "is-open" : ""}`}><NavLink to="/" onClick={close}>Discover</NavLink><NavLink to="/upload-selfie" onClick={close}>Find photos</NavLink>{user && <NavLink to="/my-gallery" onClick={close}>My gallery</NavLink>}{user && <NavLink to="/events" onClick={close}>Events</NavLink>}{user && <NavLink to="/people" onClick={close}>People</NavLink>}
      {user ? <><NavLink className="profile-link" to="/profile" onClick={close}><span className="nav-avatar">{user.avatar_url ? <img src={user.avatar_url} alt="" /> : user.full_name.charAt(0).toUpperCase()}</span>{user.full_name}</NavLink><button className="signout-button" onClick={() => { signOut(); close(); navigate("/"); }}>Sign out</button></> : <Link className="nav-cta" to="/signin" onClick={close}>Sign in</Link>}
    </div>
  </nav>;
}
