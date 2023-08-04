const request = require('supertest');
const app = require('./app');



// Teste para verificar a rota de envio de CPFs
describe('POST /send-cpfs', () => {
  it('Deve retornar a mensagem de requisição enviada com sucesso', async () => {
    const cpfList = ['123.456.789-10', '987.654.321-00'];
    const res = await request(app).post('/send-cpfs').send({ cpfList });
    expect(res.status).toBe(200);
    expect(res.body.message).toBe('Requisição enviada com sucesso!');
  });

});

// Teste para verificar a rota de busca por CPF
describe('GET /buscar/:cpf', () => {
  it('Deve retornar os dados do CPF informado', async () => {
    const cpf = '123.456.789-10'; // Substitua pelo CPF existente no Elasticsearch
    const res = await request(app).get(`/buscar/${cpf}`);
    expect(res.status).toBe(200);
    // Adicione mais verificações para os dados retornados conforme necessário
  });

  it('Deve retornar mensagem de não encontrado para um CPF inexistente', async () => {
    const cpf = '111.111.111-11'; // Substitua por um CPF inexistente no Elasticsearch
    const res = await request(app).get(`/buscar/${cpf}`);
    expect(res.status).toBe(200); // O código pode ser 200 caso o Elasticsearch não retorne um erro específico
    expect(res.body.message).toBe('Nenhuma correspondência encontrada para o CPF informado.');
  });
});
