package com.example.demo.repositories;

import com.example.demo.entities.AtendimentoPacienteV;
import org.springframework.data.jpa.repository.JpaRepository;

import java.time.LocalDate;
import java.util.List;

public interface AtendimentPacienteRepositories extends JpaRepository<AtendimentoPacienteV, Long> {
    List<AtendimentoPacienteV> findAllByDtEntradaAfter(LocalDate date);
}
