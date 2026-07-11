CREATE TABLE `Profil`(
    `Matricule` VARCHAR(50) NOT NULL,
    `Noms` VARCHAR(255) NOT NULL,
    `Prénoms` VARCHAR(255) NOT NULL,
    `email` VARCHAR(255) NOT NULL,
    `Sexe` ENUM('') NOT NULL,
    `Photo_de_profil` VARCHAR(255) NOT NULL,
    `Telephone` VARCHAR(255) NOT NULL,
    `Password` VARCHAR(255) NOT NULL,
    `login_date` DATE NOT NULL,
    PRIMARY KEY(`Matricule`)
);
ALTER TABLE
    `Profil` ADD UNIQUE `profil_email_unique`(`email`);
ALTER TABLE
    `Profil` ADD UNIQUE `profil_telephone_unique`(`Telephone`);
CREATE TABLE `Score`(
    `id` INT NOT NULL,
    `Matricule` VARCHAR(255) NULL,
    `valeur` TINYINT NOT NULL,
    PRIMARY KEY(`id`)
);
CREATE TABLE `Session_activite`(
    `id` BIGINT NOT NULL,
    `Matricule` VARCHAR(255) NOT NULL,
    `heure_debut` DATETIME NOT NULL,
    `heure_fin` BIGINT NOT NULL,
    PRIMARY KEY(`id`)
);
CREATE TABLE `application`(
    `id_application` BIGINT NOT NULL,
    `id_session` BIGINT NOT NULL,
    `nom` VARCHAR(255) NOT NULL,
    `temps_debut` DATETIME NOT NULL,
    `temps_fin` DATETIME NOT NULL,
    PRIMARY KEY(`id_application`)
);
CREATE TABLE `bad_action`(
    `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
    `id_application` BIGINT NOT NULL,
    `date` DATETIME NOT NULL,
    `titre` VARCHAR(100) NOT NULL,
    `text_input` TEXT NOT NULL,
    `conclusion` TEXT NOT NULL,
    `remove_point` TINYINT NOT NULL
);
ALTER TABLE
    `Session_activite` ADD CONSTRAINT `session_activite_matricule_foreign` FOREIGN KEY(`Matricule`) REFERENCES `Profil`(`Matricule`);
ALTER TABLE
    `application` ADD CONSTRAINT `application_id_session_foreign` FOREIGN KEY(`id_session`) REFERENCES `Session_activite`(`id`);
ALTER TABLE
    `bad_action` ADD CONSTRAINT `bad_action_id_application_foreign` FOREIGN KEY(`id_application`) REFERENCES `application`(`id_application`);
ALTER TABLE
    `Score` ADD CONSTRAINT `score_matricule_foreign` FOREIGN KEY(`Matricule`) REFERENCES `Profil`(`Matricule`);