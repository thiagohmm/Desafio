import React, { useState } from 'react';
import axios from 'axios';

const SearchCompon = () => {
  const [cpf, setCpf] = useState('');
  const [matriculas, setMatriculas] = useState([]);

  const handleSearch = async () => {
    try {
      const response = await axios.get(`/buscar/${cpf}`);
      setMatriculas(response.data.nb);

    } catch (error) {
      console.error('Error searching for matricula:', error);
    }
  };

  return (
    <div>
      <h1>Buscar Matrícula</h1>
      <input
        type="text"
        value={cpf}
        onChange={(e) => setCpf(e.target.value)}
        placeholder="Digite o CPF"
      />
      <button onClick={handleSearch}>Buscar</button>

      <h2>Resultado da Busca</h2>

      <p>CPF: {cpf}</p>
      {matriculas !== "Matrícula não encontrada!" ? (
        <ul>
          Número do Beneficio: {matriculas}
        </ul>
      ) : (
        <p>Nenhum Número de Beneficio encontrado para o CPF informado.</p>
      )}
    </div>
  );
};

export default SearchCompon;
