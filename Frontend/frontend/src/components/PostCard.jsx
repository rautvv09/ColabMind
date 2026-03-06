import React from "react";
import { RiHeartLine, RiChat1Line, RiEyeLine } from "react-icons/ri";

export default function PostCard({ post }) {
  const { post_url, post_likes, post_comments, post_views, deal_type, agreed_price } = post;

  return (
    <div className="cm-card" style={{ padding: 16 }}>
      <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 12 }}>
        <span style={{
          background: "rgba(108,99,255,0.15)", color: "var(--accent)",
          padding: "3px 10px", borderRadius: 20, fontSize: "0.75rem", fontWeight: 600
        }}>
          {deal_type || "Post"}
        </span>
        {agreed_price > 0 && (
          <span style={{ color: "var(--accent2)", fontWeight: 700, fontSize: "0.9rem" }}>
            ₹{agreed_price?.toLocaleString()}
          </span>
        )}
      </div>

      <div style={{ display: "flex", gap: 20, marginTop: 8 }}>
        <span style={{ color: "var(--text-muted)", fontSize: "0.85rem" }}>
          <RiHeartLine /> {post_likes?.toLocaleString() || 0}
        </span>
        <span style={{ color: "var(--text-muted)", fontSize: "0.85rem" }}>
          <RiChat1Line /> {post_comments?.toLocaleString() || 0}
        </span>
        <span style={{ color: "var(--text-muted)", fontSize: "0.85rem" }}>
          <RiEyeLine /> {post_views?.toLocaleString() || 0}
        </span>
      </div>

      {post_url && (
        <a href={post_url} target="_blank" rel="noreferrer"
          style={{ display: "block", marginTop: 12, color: "var(--accent)", fontSize: "0.8rem" }}>
          View Post →
        </a>
      )}
    </div>
  );
}
