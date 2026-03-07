import React, { useState } from "react";
import { getCollaborationById } from "../services/api";
import "./CollaborationHistory.css";

export default function GetCollaboration() {

  const [collabId, setCollabId] = useState("");
  const [data, setData] = useState(null);

  const handleSearch = async (e) => {

    e.preventDefault();

    try {

      const res = await getCollaborationById(collabId);

      setData(res.data.data);

    } catch (err) {

      console.error(err);
      setData(null);

    }

  };

  return (

    <div>

      <h1 className="page-title">Get Collaboration</h1>

      <form onSubmit={handleSearch} className="collab-form">

        <input
          className="cm-input"
          placeholder="Enter Collaboration ID"
          value={collabId}
          onChange={(e) => setCollabId(e.target.value)}
          required
        />

        <button className="btn-cm">
          Search
        </button>

      </form>

      {data && (

        <div className="cm-card" style={{marginTop:20}}>

          <p><b>Deal:</b> {data.deal_type}</p>
          <p><b>Status:</b> {data.status}</p>
          <p><b>Payment:</b> {data.payment_status}</p>
          <p><b>Price:</b> ₹{data.agreed_price}</p>
          <p><b>Deadline:</b> {data.deadline}</p>

        </div>

      )}

    </div>

  );
}